from __future__ import annotations

from tempfile import TemporaryDirectory

from observable_agent_workflow_memory.adapters.jsonschema_checker import create_default_checkers
from observable_agent_workflow_memory.adapters.semantic_checkers import ReplaySuccessChecker
from observable_agent_workflow_memory.core.models import Lane
from observable_agent_workflow_memory.runtime.kernel import AgentKernel


def main() -> None:
    with TemporaryDirectory(prefix="oawm-semantic-", ignore_cleanup_errors=True) as state:
        kernel = AgentKernel.open(
            state,
            plugins={"checkers": [*create_default_checkers(), ReplaySuccessChecker()]},
        )
        kernel.observe("note", {"text": "workflow must replay successfully"}, run_id="demo")
        candidate = kernel.propose_memory("demo")
        evidence = kernel.promotion.build_evidence(candidate)

        failed = kernel.promotion.verify(candidate.memory_id, evidence=evidence)
        print({"without_replay_success": failed.result})

        candidate = kernel.storage.get_memory_record(candidate.memory_id)
        candidate = candidate.moved(Lane.CANDIDATE, reason="retry with explicit replay evidence")
        kernel.storage.upsert_memory_record(candidate)
        evidence = kernel.promotion.build_evidence(candidate)
        passed = kernel.promotion.verify(
            candidate.memory_id,
            evidence=evidence,
            context={"replay_success": True},
        )
        print({"with_replay_success": passed.result})


if __name__ == "__main__":
    main()
