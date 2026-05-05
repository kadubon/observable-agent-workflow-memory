"""Checker port."""

from __future__ import annotations

from typing import Any, Protocol

from observable_agent_workflow_memory.core.models import CheckerResult, MemoryRecord


class Checker(Protocol):
    checker_name: str

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        """Verify a memory promotion candidate."""

