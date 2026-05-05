from __future__ import annotations

from observable_agent_workflow_memory.core.models import Lane, MemoryRecord, StoredEvent


class DomainWorkflowProposer:
    proposer_name = "domain-example"

    def propose(self, events: list[StoredEvent], *, scope: str = "session") -> MemoryRecord:
        event_ids = [event.event_id for event in events]
        return MemoryRecord.create(
            lane=Lane.CANDIDATE,
            claim=f"Domain workflow candidate for {scope} from {len(events)} event(s)",
            source_event_ids=event_ids,
            metadata={
                "proposal_scope": scope,
                "interface_signature": "example.domain.workflow.v1",
                "tools": [],
                "resource_caps": {"max_steps": max(1, min(8, len(events) + 1))},
                "steps": [f"Replay {event.kind}" for event in events],
            },
        )


def create_proposer() -> DomainWorkflowProposer:
    return DomainWorkflowProposer()
