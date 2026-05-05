from __future__ import annotations

from tempfile import TemporaryDirectory

from observable_agent_workflow_memory.runtime.kernel import AgentKernel


def main() -> None:
    with TemporaryDirectory(prefix="oawm-certified-", ignore_cleanup_errors=True) as state:
        kernel = AgentKernel.open(state)
        kernel.observe("note", {"text": "collect evidence before reuse"}, run_id="demo")
        kernel.observe("note", {"text": "verify before promotion"}, run_id="demo")

        candidate = kernel.propose_memory("demo")
        raw_results = kernel.retrieve("evidence", mode="raw")
        before = kernel.retrieve("workflow candidate", mode="admissible")

        receipt = kernel.verify(candidate.memory_id)
        if receipt.result != "passed":
            raise SystemExit(receipt.model_dump_json(indent=2))
        certified = kernel.promote(candidate.memory_id)
        after = kernel.retrieve("workflow candidate", mode="admissible")

        print(
            {
                "raw_count": len(raw_results),
                "admissible_before": len(before),
                "certified_lane": certified.lane.value,
                "admissible_after": [item.memory_id for item in after],
            }
        )


if __name__ == "__main__":
    main()
