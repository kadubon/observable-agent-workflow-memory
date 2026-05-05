"""Deterministic semantic checker templates.

These checkers validate explicit evidence records. They do not make model
judgments and do not prove factual truth.
"""

from __future__ import annotations

from typing import Any

from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.models import CheckerResult, MemoryRecord


class ReplaySuccessChecker:
    checker_name = "replay-success"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        del candidate
        replay_success = _evidence_or_context(evidence, context, "replay_success")
        if replay_success is not True:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="replay_success must be explicitly true",
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class ToolTraceChecker:
    checker_name = "tool-trace"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        declared_tools = candidate.metadata.get("tools", [])
        if not isinstance(declared_tools, list) or not all(
            isinstance(tool, str) for tool in declared_tools
        ):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="candidate metadata tools must be a list of strings",
            )
        invocations = _evidence_or_context(evidence, context, "tool_invocations")
        if not isinstance(invocations, list) or not invocations:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="tool_invocations evidence must be a non-empty list",
            )
        for index, invocation in enumerate(invocations):
            if not isinstance(invocation, dict):
                return CheckerResult(
                    checker_name=self.checker_name,
                    passed=False,
                    reason=f"tool invocation {index} must be an object",
                )
            tool_name = invocation.get("tool_name")
            if not isinstance(tool_name, str) or tool_name not in declared_tools:
                return CheckerResult(
                    checker_name=self.checker_name,
                    passed=False,
                    reason=f"tool invocation {index} is undeclared: {tool_name}",
                )
            args_digest = invocation.get("args_digest")
            if args_digest is not None:
                arguments = invocation.get("arguments")
                if not isinstance(args_digest, str) or not isinstance(arguments, dict):
                    return CheckerResult(
                        checker_name=self.checker_name,
                        passed=False,
                        reason=f"tool invocation {index} needs arguments with args_digest",
                    )
                observed = digest_json(arguments)
                if observed != args_digest:
                    return CheckerResult(
                        checker_name=self.checker_name,
                        passed=False,
                        reason=f"tool invocation {index} args_digest mismatch",
                        metrics={"expected": args_digest, "observed": observed},
                    )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class DomainInvariantChecker:
    checker_name = "domain-invariant"

    def __init__(self, required_invariants: list[str] | None = None) -> None:
        self.required_invariants = required_invariants or []

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        del candidate
        invariant_results = _evidence_or_context(evidence, context, "invariant_results")
        if not isinstance(invariant_results, dict):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="invariant_results must be an object mapping labels to booleans",
            )
        missing = [
            invariant
            for invariant in self.required_invariants
            if invariant_results.get(invariant) is not True
        ]
        if missing:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"required invariants did not pass: {missing}",
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


def _evidence_or_context(evidence: dict[str, Any], context: dict[str, Any], key: str) -> Any:
    if key in evidence:
        return evidence[key]
    return context.get(key)
