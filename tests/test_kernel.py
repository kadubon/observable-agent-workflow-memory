from __future__ import annotations

import pytest

from observable_agent_workflow_memory.core.errors import FailClosedError
from observable_agent_workflow_memory.core.models import ActionIntent, Lane, MemoryRecord
from observable_agent_workflow_memory.ports.tools import ToolCall
from observable_agent_workflow_memory.runtime.kernel import AgentKernel


def test_observe_propose_verify_promote_retrieve_cycle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    kernel.observe("note", {"text": "collect evidence before reusing workflow"}, run_id="demo")
    kernel.observe("note", {"text": "verify receipts before promotion"}, run_id="demo")
    candidate = kernel.propose_memory("demo")

    assert candidate.lane == Lane.CANDIDATE
    assert kernel.retrieve("workflow", mode="admissible") == []

    receipt = kernel.verify(candidate.memory_id)
    assert receipt.result == "passed"
    shadow = kernel.storage.get_memory_record(candidate.memory_id)
    assert shadow.lane == Lane.SHADOW
    verify_event = [
        event
        for event in kernel.storage.list_events(run_id="demo")
        if event.kind == "memory_verify"
    ][-1]
    assert verify_event.payload["memory_refs"][0]["memory_id"] == candidate.memory_id
    assert verify_event.payload["memory_refs"][0]["update_id"] == candidate.update_id
    assert verify_event.payload["memory_refs"][0]["content_digest"] == candidate.content_digest()
    assert kernel.audit()["events"] == 4

    certified = kernel.promote(candidate.memory_id)
    assert certified.lane == Lane.CERTIFIED
    revisions = kernel.storage.list_memory_revisions(memory_id=candidate.memory_id)
    assert [revision.after_lane for revision in revisions[-3:]] == [
        Lane.CANDIDATE,
        Lane.SHADOW,
        Lane.CERTIFIED,
    ]

    results = kernel.retrieve("workflow", mode="admissible")
    assert [item.lane for item in results] == [Lane.CERTIFIED]

    assert certified.workflow_contract_id is not None
    contract = kernel.storage.get_contract(certified.workflow_contract_id)
    assert "evidence-manifest" in contract.checkers


def test_retrieve_records_read_without_new_raw_memory(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "raw item"}, run_id="demo")

    before = kernel.audit()
    kernel.retrieve("raw item", mode="raw", run_id="demo")
    after = kernel.audit()

    assert after["events"] == before["events"] + 1
    assert after["raw"] == before["raw"]


def test_missing_evidence_fails_closed_and_quarantines(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    kernel.observe("note", {"text": "candidate needs evidence"}, run_id="demo")
    candidate = kernel.propose_memory("demo")
    receipt = kernel.promotion.verify(candidate.memory_id, evidence={})

    assert receipt.result == "failed"
    stored = kernel.storage.get_memory_record(candidate.memory_id)
    assert stored.lane == Lane.QUARANTINE

    with pytest.raises(FailClosedError):
        kernel.promote(candidate.memory_id)


def test_repeated_verify_appends_distinct_receipts(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "append-only receipt evidence"}, run_id="demo")
    candidate = kernel.propose_memory("demo")

    first = kernel.verify(candidate.memory_id)
    second = kernel.verify(candidate.memory_id)
    receipts = kernel.storage.list_receipts(candidate_id=candidate.memory_id)

    assert first.result == "passed"
    assert second.result == "passed"
    assert first.receipt_id != second.receipt_id
    assert first.receipt_digest == second.receipt_digest
    assert [item.receipt_id for item in receipts] == [first.receipt_id, second.receipt_id]


def test_verify_receipt_detects_digest_tampering(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "receipt audit evidence"}, run_id="demo")
    candidate = kernel.propose_memory("demo")
    receipt = kernel.verify(candidate.memory_id)

    assert kernel.verify_receipt(receipt.receipt_id).passed is True

    tampered = receipt.model_copy(
        update={"receipt_id": "rcp_" + "0" * 32, "receipt_digest": "tampered"}
    )
    kernel.storage.create_receipt(tampered)

    result = kernel.verify_receipt(tampered.receipt_id)
    assert result.passed is False
    assert "receipt_digest mismatch" in result.reason


def test_action_intent_resource_caps_mismatch_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "caps evidence"}, run_id="gate")
    candidate = kernel.propose_memory("gate", tools=["kernel.run"], resource_caps={"max_steps": 2})
    intent = ActionIntent.create(
        tool_name="kernel.run",
        effect_class="external",
        arguments={"task": "caps mismatch"},
        resource_caps={"max_steps": 99},
    )

    receipt = kernel.verify(candidate.memory_id, action_intent=intent)

    assert receipt.result == "failed"
    assert kernel.storage.get_memory_record(candidate.memory_id).lane == Lane.QUARANTINE


def test_tampered_input_event_digest_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    kernel.observe("note", {"text": "digest-bound evidence"}, run_id="demo")
    candidate = kernel.propose_memory("demo")
    evidence = kernel.promotion.build_evidence(candidate)
    evidence["input_event_digests"][candidate.source_event_ids[0]] = "tampered"

    receipt = kernel.promotion.verify(candidate.memory_id, evidence=evidence)

    assert receipt.result == "failed"
    stored = kernel.storage.get_memory_record(candidate.memory_id)
    assert stored.lane == Lane.QUARANTINE


def test_tampered_replay_digest_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    kernel.observe("note", {"text": "replay-bound evidence"}, run_id="demo")
    candidate = kernel.propose_memory("demo")
    evidence = kernel.promotion.build_evidence(candidate)
    evidence["replay_digest"] = "tampered"

    receipt = kernel.promotion.verify(candidate.memory_id, evidence=evidence)

    assert receipt.result == "failed"
    stored = kernel.storage.get_memory_record(candidate.memory_id)
    assert stored.lane == Lane.QUARANTINE


def test_tampered_manifest_id_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    kernel.observe("note", {"text": "manifest-bound evidence"}, run_id="demo")
    candidate = kernel.propose_memory("demo")
    evidence = kernel.promotion.build_evidence(candidate)
    evidence["manifest_id"] = "evm_tampered"

    receipt = kernel.promotion.verify(candidate.memory_id, evidence=evidence)

    assert receipt.result == "failed"
    stored = kernel.storage.get_memory_record(candidate.memory_id)
    assert stored.lane == Lane.QUARANTINE


def test_inputset_must_exactly_match_candidate_sources(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    event = kernel.observe("note", {"text": "exact inputset"}, run_id="demo")
    candidate = kernel.propose_memory("demo")
    evidence = kernel.promotion.build_evidence(candidate)
    evidence["input_event_ids"] = [event.event_id, "evt_extra"]

    receipt = kernel.promotion.verify(candidate.memory_id, evidence=evidence)

    assert receipt.result == "failed"
    assert kernel.storage.get_memory_record(candidate.memory_id).lane == Lane.QUARANTINE


def test_float_in_decision_critical_candidate_fails_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "candidate with float metadata"}, run_id="float")
    candidate = kernel.propose_memory("float")
    data = candidate.model_dump()
    data["metadata"]["resource_caps"] = {"max_steps": 4}
    data["metadata"]["unstable_score"] = 0.25
    candidate = type(candidate)(**data)
    kernel.storage.upsert_memory_record(candidate)

    receipt = kernel.verify(candidate.memory_id)

    assert receipt.result == "failed"
    assert kernel.storage.get_memory_record(candidate.memory_id).lane == Lane.QUARANTINE


def test_correct_memory_creates_verified_superseding_candidate(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "old workflow"}, run_id="demo")
    original = kernel.propose_memory("demo")
    kernel.verify(original.memory_id)
    certified = kernel.promote(original.memory_id)

    correction = kernel.correct_memory(
        certified.memory_id,
        "corrected workflow contract claim",
        run_id="demo-correction",
    )
    receipt = kernel.verify(correction.memory_id)
    promoted = kernel.promote(correction.memory_id)

    assert receipt.result == "passed"
    assert promoted.lane == Lane.CERTIFIED
    assert promoted.supersedes == [certified.memory_id]
    assert kernel.storage.get_memory_record(certified.memory_id).lane == Lane.SUPERSEDED


def test_external_effects_are_blocked_without_gate_receipt(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)

    with pytest.raises(FailClosedError):
        kernel.run("do something irreversible", external_effects=True)


def test_external_effects_require_action_bound_receipt(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.observe("note", {"text": "gate evidence"}, run_id="gate")
    candidate = kernel.propose_memory("gate")
    candidate = _candidate_with_tools(kernel, candidate, ["kernel.run"])
    receipt = kernel.verify(candidate.memory_id)

    intent = ActionIntent.create(
        tool_name="kernel.run",
        effect_class="external",
        arguments={"task": "allowed external effect declaration"},
        resource_caps=candidate.metadata["resource_caps"],
    )
    bound_receipt = kernel.verify(candidate.memory_id, action_intent=intent)
    gated_intent = ActionIntent.create(
        tool_name="kernel.run",
        effect_class="external",
        arguments={"task": "allowed external effect declaration"},
        required_receipt_id=bound_receipt.receipt_id,
        resource_caps=candidate.metadata["resource_caps"],
    )

    with pytest.raises(FailClosedError):
        kernel.run(
            "allowed external effect declaration",
            external_effects=True,
            gate_receipt_ids=[receipt.receipt_id],
            action_intent=gated_intent,
        )

    result = kernel.run(
        "allowed external effect declaration",
        external_effects=True,
        gate_receipt_ids=[bound_receipt.receipt_id],
        action_intent=gated_intent,
    )
    assert "allowed external effect declaration" in result.content


def test_kernel_invoke_tool_checks_action_digest_and_adapter_token(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(tmp_path)
    kernel.tool_adapter.register("write", lambda args, _context: {"seen": args["value"]})
    kernel.observe("note", {"text": "tool gate evidence"}, run_id="gate")
    candidate = kernel.propose_memory("gate")
    candidate = _candidate_with_tools(kernel, candidate, ["write"])
    intent = ActionIntent.create(
        tool_name="write",
        effect_class="local-external",
        arguments={"value": "ok"},
        resource_caps=candidate.metadata["resource_caps"],
    )
    receipt = kernel.verify(candidate.memory_id, action_intent=intent)
    gated_intent = ActionIntent.create(
        tool_name="write",
        effect_class="local-external",
        arguments={"value": "ok"},
        required_receipt_id=receipt.receipt_id,
        resource_caps=candidate.metadata["resource_caps"],
    )

    result = kernel.invoke_tool(
        ToolCall(name="write", arguments={"value": "ok"}, external_effect=True),
        gated_intent,
        [receipt.receipt_id],
    )
    assert result.ok is True
    assert result.output == {"seen": "ok"}

    with pytest.raises(FailClosedError):
        kernel.invoke_tool(
            ToolCall(name="write", arguments={"value": "changed"}, external_effect=True),
            gated_intent,
            [receipt.receipt_id],
        )

    with pytest.raises(FailClosedError):
        kernel.tool_adapter.invoke(
            ToolCall(name="write", arguments={"value": "ok"}, external_effect=True),
            context={"action_gate_open": True},
        )


def _candidate_with_tools(
    kernel: AgentKernel,
    candidate: MemoryRecord,
    tools: list[str],
) -> MemoryRecord:
    metadata = dict(candidate.metadata)
    metadata["tools"] = tools
    updated = MemoryRecord.create(
        lane=candidate.lane,
        claim=candidate.claim,
        source_event_ids=list(candidate.source_event_ids),
        metadata=metadata,
        evidence_refs=list(candidate.evidence_refs),
        supersedes=list(candidate.supersedes),
        contradicts=list(candidate.contradicts),
    )
    return kernel.storage.upsert_memory_record(updated)
