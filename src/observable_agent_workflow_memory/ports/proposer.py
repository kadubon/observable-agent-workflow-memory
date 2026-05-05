"""Workflow proposer port."""

from __future__ import annotations

from typing import Protocol

from observable_agent_workflow_memory.core.models import MemoryRecord, StoredEvent


class WorkflowProposer(Protocol):
    proposer_name: str

    def propose(self, events: list[StoredEvent], *, scope: str = "session") -> MemoryRecord:
        """Create a memory candidate from observable events."""
