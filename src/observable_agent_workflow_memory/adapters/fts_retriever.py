"""FTS5 retriever adapter."""

from __future__ import annotations

from typing import Protocol

from observable_agent_workflow_memory.core.models import Lane, RetrievedMemory


class SearchableMemoryStorage(Protocol):
    def search_memory(
        self,
        query: str,
        *,
        lane_filter: list[Lane],
        limit: int,
    ) -> list[RetrievedMemory]:
        """Search stored memory records."""


class FTSRetriever:
    retriever_name = "fts5"

    def __init__(self, storage: SearchableMemoryStorage) -> None:
        self.storage = storage

    def search(
        self,
        query: str,
        *,
        lane_filter: list[Lane],
        limit: int,
    ) -> list[RetrievedMemory]:
        return self.storage.search_memory(query, lane_filter=lane_filter, limit=limit)


def create_retriever(storage: SearchableMemoryStorage) -> FTSRetriever:
    return FTSRetriever(storage)
