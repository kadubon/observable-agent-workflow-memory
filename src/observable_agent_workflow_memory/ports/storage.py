"""Storage backend port."""

from __future__ import annotations

from typing import Protocol

from observable_agent_workflow_memory.core.models import (
    Event,
    EvidenceManifest,
    Lane,
    MemoryOperation,
    MemoryRecord,
    MemoryRevision,
    PromotionReceipt,
    StoredEvent,
    WorkflowContract,
)


class StorageBackend(Protocol):
    backend_name: str

    def initialize(self) -> None:
        """Create required storage structures."""

    def append_event(self, event: Event) -> StoredEvent:
        """Append one observable event."""

    def list_events(
        self,
        *,
        run_id: str | None = None,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        """Return events in observable order."""

    def get_event(self, event_id: str) -> StoredEvent:
        """Return one event by id."""

    def upsert_memory_record(
        self,
        record: MemoryRecord,
        *,
        operation: MemoryOperation = MemoryOperation.WRITE,
        reason: str = "",
        receipt_id: str | None = None,
        event_id: str | None = None,
    ) -> MemoryRecord:
        """Store or replace a memory record."""

    def get_memory_record(self, memory_id: str) -> MemoryRecord:
        """Return a memory record."""

    def list_memory_records(self, *, lane: Lane | None = None) -> list[MemoryRecord]:
        """List memory records."""

    def list_memory_revisions(self, *, memory_id: str | None = None) -> list[MemoryRevision]:
        """List append-only memory revisions."""

    def create_contract(self, contract: WorkflowContract) -> WorkflowContract:
        """Persist a workflow contract."""

    def get_contract(self, contract_id: str) -> WorkflowContract:
        """Return a workflow contract."""

    def create_receipt(self, receipt: PromotionReceipt) -> PromotionReceipt:
        """Persist a promotion receipt."""

    def get_receipt(self, receipt_id: str) -> PromotionReceipt:
        """Return a receipt."""

    def list_receipts(self, *, candidate_id: str | None = None) -> list[PromotionReceipt]:
        """List receipts."""

    def create_evidence_manifest(self, manifest: EvidenceManifest) -> EvidenceManifest:
        """Persist an evidence manifest."""

    def get_evidence_manifest(self, manifest_id: str) -> EvidenceManifest:
        """Return an evidence manifest."""

    def audit_counts(self) -> dict[str, int]:
        """Return coarse audit counts."""
