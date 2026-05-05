"""Self-improvement helper loop."""

from __future__ import annotations

from observable_agent_workflow_memory.core.models import MemoryRecord
from observable_agent_workflow_memory.runtime.kernel import AgentKernel


class SelfImprovementLoop:
    """Runs candidate generation and shadow verification after a run."""

    def __init__(self, kernel: AgentKernel) -> None:
        self.kernel = kernel

    def consolidate_run(self, run_id: str) -> MemoryRecord:
        candidate = self.kernel.propose_memory(run_id)
        self.kernel.verify(candidate.memory_id)
        return self.kernel.storage.get_memory_record(candidate.memory_id)
