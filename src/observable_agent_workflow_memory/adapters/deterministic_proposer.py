"""Deterministic workflow proposer used by default."""

from __future__ import annotations

from observable_agent_workflow_memory.core.models import Lane, MemoryRecord, StoredEvent


class DeterministicWorkflowProposer:
    proposer_name = "deterministic"

    def propose(self, events: list[StoredEvent], *, scope: str = "session") -> MemoryRecord:
        if not events:
            msg = "cannot propose memory without observable events"
            raise ValueError(msg)
        event_ids = [event.event_id for event in events]
        kinds = ", ".join(sorted({event.kind for event in events}))
        claim = f"Workflow candidate from {len(events)} observable event(s): {kinds}"
        metadata = {
            "scope": scope,
            "steps": [event.kind for event in events],
            "tools": [],
            "resource_caps": {"max_steps": max(1, min(32, len(events) + 1))},
            "input_event_ids": event_ids,
        }
        return MemoryRecord.create(
            lane=Lane.CANDIDATE,
            claim=claim,
            source_event_ids=event_ids,
            metadata=metadata,
        )


def create_proposer() -> DeterministicWorkflowProposer:
    return DeterministicWorkflowProposer()
