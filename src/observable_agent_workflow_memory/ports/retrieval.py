"""Retriever port."""

from __future__ import annotations

from typing import Protocol

from observable_agent_workflow_memory.core.models import Lane, RetrievedMemory


class Retriever(Protocol):
    retriever_name: str

    def search(
        self,
        query: str,
        *,
        lane_filter: list[Lane],
        limit: int,
    ) -> list[RetrievedMemory]:
        """Search memory records."""

