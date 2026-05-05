"""Reusable contract checks for plugin authors."""

from __future__ import annotations

from observable_agent_workflow_memory.core.models import Event, EvidenceManifest, Lane, MemoryRecord
from observable_agent_workflow_memory.ports.checker import Checker
from observable_agent_workflow_memory.ports.llm import LLMMessage, LLMProvider
from observable_agent_workflow_memory.ports.storage import StorageBackend


def assert_llm_provider_contract(provider: LLMProvider) -> None:
    result = provider.complete([LLMMessage(role="user", content="contract check")])
    assert isinstance(result.content, str)
    assert result.content


def assert_checker_contract(checker: Checker) -> None:
    event_id = "evt_contract"
    candidate = MemoryRecord.create(
        lane=Lane.CANDIDATE,
        claim="contract-check candidate",
        source_event_ids=[event_id],
    )
    result = checker.verify(
        candidate,
        evidence={
            "input_event_ids": [event_id],
            "candidate_digest": candidate.content_digest(),
        },
        context={},
    )
    assert isinstance(result.passed, bool)
    assert result.checker_name


def assert_storage_backend_contract(storage: StorageBackend) -> None:
    storage.initialize()
    event = Event.create(kind="contract", payload={"text": "storage"}, run_id="contract")
    stored = storage.append_event(event)
    record = MemoryRecord.create(
        lane=Lane.RAW,
        claim="contract storage memory",
        source_event_ids=[stored.event_id],
    )
    storage.upsert_memory_record(record)
    manifest = EvidenceManifest.create(candidate=record, input_event_ids=[stored.event_id])
    storage.create_evidence_manifest(manifest)
    assert storage.get_memory_record(record.memory_id).memory_id == record.memory_id
    assert storage.list_events(run_id="contract")[0].event_id == stored.event_id
    assert storage.get_evidence_manifest(manifest.manifest_id).candidate_id == record.memory_id
    assert storage.list_memory_revisions(memory_id=record.memory_id)
