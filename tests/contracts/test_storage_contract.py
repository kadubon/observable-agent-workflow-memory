from __future__ import annotations

import sqlite3

import pytest

from observable_agent_workflow_memory.adapters.sqlite_storage import SQLiteStorage
from observable_agent_workflow_memory.core.canonical import canonical_json
from observable_agent_workflow_memory.core.errors import FailClosedError
from observable_agent_workflow_memory.core.models import (
    CheckerResult,
    Event,
    EvidenceManifest,
    Lane,
    MemoryOperation,
    MemoryRecord,
    PromotionReceipt,
    WorkflowContract,
)


def test_sqlite_storage_round_trips_events_and_memory(tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = SQLiteStorage(tmp_path / "state.sqlite")
    storage.initialize()

    event = Event.create(kind="note", payload={"text": "hello"}, run_id="run-test")
    stored = storage.append_event(event)
    raw = MemoryRecord.create(
        lane=Lane.RAW,
        claim="note: hello",
        source_event_ids=[stored.event_id],
    )
    storage.upsert_memory_record(raw)
    manifest = EvidenceManifest.create(
        candidate=raw,
        input_event_ids=[stored.event_id],
    )
    storage.create_evidence_manifest(manifest)

    assert storage.list_events(run_id="run-test")[0].event_id == event.event_id
    assert storage.get_memory_record(raw.memory_id).claim == "note: hello"
    assert storage.get_evidence_manifest(manifest.manifest_id).candidate_id == raw.memory_id
    assert storage.audit_counts()["events"] == 1
    revisions = storage.list_memory_revisions(memory_id=raw.memory_id)
    assert len(revisions) == 1
    assert revisions[0].operation == MemoryOperation.WRITE
    assert revisions[0].after_lane == Lane.RAW


def test_sqlite_storage_rejects_payload_digest_mismatch(tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = SQLiteStorage(tmp_path / "state.sqlite")
    storage.initialize()

    event = Event.create(kind="note", payload={"text": "hello"}, run_id="run-test")
    tampered = event.model_copy(update={"payload_digest": "tampered"})

    with pytest.raises(FailClosedError):
        storage.append_event(tampered)


def test_workflow_contracts_are_idempotent_not_replaceable(tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = SQLiteStorage(tmp_path / "state.sqlite")
    storage.initialize()
    candidate = MemoryRecord.create(
        lane=Lane.SHADOW,
        claim="contract candidate",
        source_event_ids=["evt_contract"],
        metadata={"resource_caps": {"max_steps": 2}},
    )
    receipt = PromotionReceipt.create(
        candidate=candidate,
        profile="strict",
        checks=[CheckerResult(checker_name="contract", passed=True)],
        evidence_refs=["evm_contract"],
    )
    contract = WorkflowContract.from_candidate(candidate, receipt)

    storage.create_contract(contract)
    storage.create_contract(contract)
    changed = contract.model_copy(update={"description": "tampered"})

    with pytest.raises(FailClosedError):
        storage.create_contract(changed)


def test_sqlite_migrates_v10_receipt_and_manifest_ordering(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE promotion_receipts (
                receipt_id TEXT PRIMARY KEY,
                candidate_id TEXT,
                result TEXT,
                raw_json TEXT
            )
            """
        )
        con.execute(
            """
            CREATE TABLE evidence_manifests (
                manifest_id TEXT PRIMARY KEY,
                candidate_id TEXT,
                raw_json TEXT
            )
            """
        )
        candidate = MemoryRecord.create(
            lane=Lane.CANDIDATE,
            claim="legacy candidate",
            source_event_ids=["evt_legacy"],
        )
        manifest = EvidenceManifest.create(candidate=candidate, input_event_ids=["evt_legacy"])
        receipt = PromotionReceipt.create(
            candidate=candidate,
            profile="strict",
            checks=[CheckerResult(checker_name="legacy", passed=True)],
            evidence_refs=[manifest.manifest_id],
        )
        legacy_receipt = receipt.model_dump(mode="json")
        legacy_receipt.pop("verification_id")
        legacy_receipt.pop("receipt_digest")
        legacy_receipt.pop("candidate_update_id")
        legacy_manifest = manifest.model_dump(mode="json")
        legacy_manifest.pop("candidate_update_id")
        con.execute(
            "INSERT INTO promotion_receipts VALUES (?, ?, ?, ?)",
            (
                receipt.receipt_id,
                receipt.candidate_id,
                receipt.result,
                canonical_json(legacy_receipt),
            ),
        )
        con.execute(
            "INSERT INTO evidence_manifests VALUES (?, ?, ?)",
            (manifest.manifest_id, manifest.candidate_id, canonical_json(legacy_manifest)),
        )

    storage = SQLiteStorage(db_path)
    storage.initialize()

    assert storage.list_receipts()[0].receipt_id == receipt.receipt_id
    assert storage.get_evidence_manifest(manifest.manifest_id).manifest_id == manifest.manifest_id
    assert storage.audit_counts()["memory_revisions"] == 0
