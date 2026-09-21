"""Fresh authoritative checks; retriever labels and summary flags have no authority."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from observable_agent_workflow_memory.adapters.jsonschema_checker import create_default_checkers
from observable_agent_workflow_memory.adapters.receipt_verifier import DefaultReceiptVerifier
from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.models import (
    EvidenceManifest,
    Lane,
    MemoryRecord,
    PromotionReceipt,
    WorkflowContract,
)

from .native import reconstruct
from .wire import Context, Qualification, digest, loads


def row(con: sqlite3.Connection, table: str, key: str, value: str) -> dict[str, Any]:
    allowed = {
        ("memory_records", "memory_id"),
        ("workflow_contracts", "contract_id"),
        ("promotion_receipts", "receipt_id"),
        ("evidence_manifests", "manifest_id"),
        ("events", "event_id"),
    }
    if (table, key) not in allowed:
        raise ValueError("unknown record lookup")
    result = con.execute(f"SELECT raw_json FROM {table} WHERE {key}=?", (value,)).fetchone()
    if result is None:
        raise ValueError("missing authoritative record")
    return dict(json.loads(result[0]))


def promotion(con: sqlite3.Connection, q: Qualification) -> MemoryRecord:
    memory = MemoryRecord.model_validate(row(con, "memory_records", "memory_id", q.memory_id))
    if (
        memory.lane != Lane.CERTIFIED
        or memory.update_id != q.update_id
        or memory.content_digest() != q.workflow_digest
    ):
        raise ValueError("current promotion or memory revision mismatch")
    if memory.update_id != MemoryRecord.compute_update_id(
        memory.memory_id, memory.content_digest()
    ):
        raise ValueError("memory content binding mismatch")
    receipt = PromotionReceipt.model_validate(
        row(con, "promotion_receipts", "receipt_id", memory.receipt_id or "")
    )
    contract = WorkflowContract.model_validate(
        row(con, "workflow_contracts", "contract_id", memory.workflow_contract_id or "")
    )
    if (
        not receipt.checks
        or receipt.result != "passed"
        or any(not c.passed for c in receipt.checks)
    ):
        raise ValueError("empty or failed promotion checks")
    manifest_id = next((s for s in receipt.evidence_refs if s.startswith("evm_")), "")
    manifest = EvidenceManifest.model_validate(
        row(con, "evidence_manifests", "manifest_id", manifest_id)
    )
    if not DefaultReceiptVerifier().verify_receipt(receipt, manifest, {"candidate": memory}).passed:
        raise ValueError("receipt binding failed")
    if (
        contract.source_update_id != memory.update_id
        or contract.source_memory_id != memory.memory_id
        or contract.replay_spec.get("receipt_id") != receipt.receipt_id
    ):
        raise ValueError("workflow receipt mismatch")
    event_digests = {}
    for identity in memory.source_event_ids:
        observed = row(con, "events", "event_id", identity)
        if digest_json(observed["payload"]) != observed["payload_digest"]:
            raise ValueError("authoritative event corruption")
        event_digests[identity] = observed["payload_digest"]
    for checker in create_default_checkers():
        if not checker.verify(
            memory.model_copy(update={"lane": Lane.SHADOW}),
            evidence=manifest.model_dump(mode="json"),
            context={"actual_event_digests": event_digests, "missing_source_event_ids": []},
        ).passed:
            raise ValueError("promotion recheck failed: " + checker.checker_name)
    if set(memory.source_event_ids) != {s.event_id for s in q.training}:
        raise ValueError("unmapped memory source events")
    for source in q.training + q.evaluation:
        original = row(con, "events", "event_id", source.event_id)
        if (
            original["kind"] != "registered_operation"
            or original["payload"].get("raw") != source.raw
            or source.producer_digest != digest_json(loads(source.raw))
        ):
            raise ValueError("source bytes not authoritative local observations")
        if digest_json(original["payload"]) != original["payload_digest"]:
            raise ValueError("observed envelope digest mismatch")
    return memory


def decision(
    con: sqlite3.Connection,
    q: Qualification,
    context: Context,
    input_text: str,
    now: int,
    state: dict[str, Any],
) -> dict[str, Any]:
    reasons = []
    if type(now) is not int or not 0 <= now <= 2**31:
        raise ValueError("trusted integer time required")
    if q.context != context or input_text not in context.inputs:
        reasons.append("receiver_context_or_input_mismatch")
    if not context.expose:
        reasons.append("host_exposure_not_permitted")
    if not q.valid_from <= now < q.valid_until:
        reasons.append("outside_validity")
    if any(c.model_dump() != state["costs"].get(c.id) for c in q.costs):
        reasons.append("unpaid_cost")
    if any(item["dependency"] in context.dependencies for item in state["withdrawn"]):
        reasons.append("dependency_withdrawn")
    for block in state["blocks"]:
        if (
            block["artifact"] == q.candidate.get("artifact_digest")
            and block["context"] == digest(context)
            and block["input"] == input_text
            and q.valid_from <= block["time"]
        ):
            reasons.append("scoped_invalidation:" + block["event"])
    try:
        promotion(con, q)
        reconstruct(q, now)
    except (ValueError, KeyError) as exc:
        reasons.append(str(exc))
    return {
        "parse_valid": True,
        "binding_checks": not reasons,
        "structural_qualification": "native-ALT-source-replay" if not reasons else None,
        "source_authentication": None,
        "semantic_evidence_scope": "finite normalize-lines inputs only; host-recorded",
        "current_memory_eligibility": "eligible" if not reasons else "blocked",
        "execution_authority": None,
        "reasons": reasons,
        "snapshot": state["revision"],
        "qualification": digest(q),
        "memory_id": q.memory_id,
        "update_id": q.update_id,
        "workflow_digest": q.workflow_digest,
        "context_digest": digest(context),
        "expiry": q.valid_until,
        "dependency_status": "current"
        if not any("withdrawn" in r for r in reasons)
        else "withdrawn",
        "unsupported_fields": ["remote authentication", "host execution permission"],
        "residuals": [],
    }
