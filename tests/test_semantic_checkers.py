from __future__ import annotations

from observable_agent_workflow_memory.adapters.semantic_checkers import (
    DomainInvariantChecker,
    ReplaySuccessChecker,
    ToolTraceChecker,
)
from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.models import Lane, MemoryRecord


def _candidate() -> MemoryRecord:
    return MemoryRecord.create(
        lane=Lane.CANDIDATE,
        claim="semantic checker candidate",
        source_event_ids=["evt_semantic"],
        metadata={"tools": ["compile"], "resource_caps": {"max_steps": 4}},
    )


def test_replay_success_checker_fails_closed_and_passes() -> None:
    checker = ReplaySuccessChecker()
    candidate = _candidate()

    assert checker.verify(candidate, evidence={}, context={}).passed is False
    malformed = checker.verify(
        candidate,
        evidence={"replay_success": "true"},
        context={},
    )
    assert malformed.passed is False
    assert checker.verify(candidate, evidence={"replay_success": True}, context={}).passed is True


def test_tool_trace_checker_fails_closed_and_passes() -> None:
    checker = ToolTraceChecker()
    candidate = _candidate()
    arguments = {"target": "tests"}

    assert checker.verify(candidate, evidence={}, context={}).passed is False
    assert (
        checker.verify(
            candidate,
            evidence={"tool_invocations": "compile"},
            context={},
        ).passed
        is False
    )
    assert (
        checker.verify(
            candidate,
            evidence={"tool_invocations": [{"tool_name": "deploy"}]},
            context={},
        ).passed
        is False
    )
    assert (
        checker.verify(
            candidate,
            evidence={
                "tool_invocations": [
                    {
                        "tool_name": "compile",
                        "arguments": arguments,
                        "args_digest": "tampered",
                    }
                ]
            },
            context={},
        ).passed
        is False
    )
    assert (
        checker.verify(
            candidate,
            evidence={
                "tool_invocations": [
                    {
                        "tool_name": "compile",
                        "arguments": arguments,
                        "args_digest": digest_json(arguments),
                    }
                ]
            },
            context={},
        ).passed
        is True
    )


def test_domain_invariant_checker_fails_closed_and_passes() -> None:
    checker = DomainInvariantChecker(required_invariants=["tests-pass", "no-drift"])
    candidate = _candidate()

    assert checker.verify(candidate, evidence={}, context={}).passed is False
    assert (
        checker.verify(
            candidate,
            evidence={"invariant_results": ["tests-pass"]},
            context={},
        ).passed
        is False
    )
    assert (
        checker.verify(
            candidate,
            evidence={"invariant_results": {"tests-pass": True, "no-drift": False}},
            context={},
        ).passed
        is False
    )
    assert (
        checker.verify(
            candidate,
            evidence={"invariant_results": {"tests-pass": True, "no-drift": True}},
            context={},
        ).passed
        is True
    )
