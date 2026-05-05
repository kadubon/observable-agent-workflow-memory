from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from observable_agent_workflow_memory.core.models import (
    ActionIntent,
    CheckerResult,
    Event,
    EvidenceManifest,
    Lane,
    MemoryOperation,
    MemoryRecord,
    MemoryRevision,
    PromotionReceipt,
    StoredEvent,
    WorkflowContract,
    now_utc,
)

SCHEMA_DIR = Path(__file__).parents[1] / "schemas"


def test_public_schemas_accept_model_dumps() -> None:
    event = Event.create(kind="note", payload={"text": "schema evidence"}, run_id="schema")
    stored_event = StoredEvent(
        **event.model_dump(),
        obs_seq=1,
        obs_time=now_utc(),
        collector_seq=1,
    )
    memory = MemoryRecord.create(
        lane=Lane.CANDIDATE,
        claim="schema-bound memory",
        source_event_ids=[event.event_id],
        metadata={"tools": [], "resource_caps": {"max_steps": 2}},
    )
    manifest = EvidenceManifest.create(
        candidate=memory,
        input_event_ids=[event.event_id],
        input_event_digests={event.event_id: event.payload_digest},
        declared_tools=[],
        resource_caps={"max_steps": 2},
    )
    receipt = PromotionReceipt.create(
        candidate=memory,
        profile="strict",
        checks=[CheckerResult(checker_name="schema", passed=True)],
        evidence_refs=[manifest.manifest_id],
    )
    contract = WorkflowContract.from_candidate(memory, receipt)
    revision = MemoryRevision.create(record=memory, operation=MemoryOperation.WRITE)
    intent = ActionIntent.create(
        tool_name="tool",
        effect_class="external",
        arguments={"value": "x"},
    )

    _validate("event.schema.json", event.model_dump(mode="json"))
    _validate("event.schema.json", stored_event.model_dump(mode="json"))
    _validate("memory_record.schema.json", memory.model_dump(mode="json"))
    _validate("evidence_manifest.schema.json", manifest.model_dump(mode="json"))
    _validate("promotion_receipt.schema.json", receipt.model_dump(mode="json"))
    _validate("workflow_contract.schema.json", contract.model_dump(mode="json"))
    _validate("memory_revision.schema.json", revision.model_dump(mode="json"))
    _validate("action_intent.schema.json", intent.model_dump(mode="json"))


def _validate(schema_name: str, payload: dict[str, Any]) -> None:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
