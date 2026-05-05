from __future__ import annotations

from tempfile import TemporaryDirectory

from observable_agent_workflow_memory.core.models import ActionIntent
from observable_agent_workflow_memory.ports.tools import ToolCall
from observable_agent_workflow_memory.runtime.kernel import AgentKernel


def main() -> None:
    with TemporaryDirectory(prefix="oawm-action-bound-", ignore_cleanup_errors=True) as state:
        kernel = AgentKernel.open(state)
        kernel.tool_adapter.register(
            "write_demo",
            lambda args, _context: {"would_write": args["path"], "text": args["text"]},
        )

        kernel.observe(
            "note",
            {"text": "The write_demo action must be receipt-gated."},
            run_id="action-demo",
        )
        candidate = kernel.propose_memory(
            "action-demo",
            tools=["write_demo"],
            resource_caps={"max_steps": 4},
        )
        intent = ActionIntent.create(
            tool_name="write_demo",
            effect_class="local-external",
            arguments={"path": "demo.txt", "text": "hello"},
            resource_caps={"max_steps": 4},
        )
        receipt = kernel.verify(candidate.memory_id, action_intent=intent)
        if receipt.result != "passed":
            raise SystemExit(receipt.model_dump_json(indent=2))

        result = kernel.invoke_tool(
            ToolCall(
                name="write_demo",
                arguments={"path": "demo.txt", "text": "hello"},
                external_effect=True,
            ),
            intent,
            [receipt.receipt_id],
        )
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
