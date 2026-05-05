from __future__ import annotations

from tempfile import TemporaryDirectory

from observable_agent_workflow_memory.core.errors import FailClosedError
from observable_agent_workflow_memory.core.models import ActionIntent
from observable_agent_workflow_memory.ports.tools import ToolCall
from observable_agent_workflow_memory.runtime.kernel import AgentKernel


def main() -> None:
    with TemporaryDirectory(prefix="oawm-action-gate-", ignore_cleanup_errors=True) as state:
        kernel = AgentKernel.open(state)
        kernel.tool_adapter.register(
            "write_demo",
            lambda args, _context: {"would_write": args["path"], "text": args["text"]},
        )
        call = ToolCall(
            name="write_demo",
            arguments={"path": "demo.txt", "text": "hello"},
            external_effect=True,
        )

        try:
            kernel.invoke_tool(
                call,
                ActionIntent.create(
                    tool_name="write_demo",
                    effect_class="local-external",
                    arguments=call.arguments,
                    resource_caps={"max_steps": 4},
                ),
                [],
            )
        except FailClosedError as exc:
            print({"blocked_without_receipt": str(exc)})

        kernel.observe("note", {"text": "write_demo needs a receipt"}, run_id="demo")
        candidate = kernel.propose_memory(
            "demo",
            tools=["write_demo"],
            resource_caps={"max_steps": 4},
        )
        intent = ActionIntent.create(
            tool_name="write_demo",
            effect_class="local-external",
            arguments=call.arguments,
            resource_caps={"max_steps": 4},
        )
        receipt = kernel.verify(candidate.memory_id, action_intent=intent)
        result = kernel.invoke_tool(call, intent, [receipt.receipt_id])
        print(result.model_dump(mode="json"))

        try:
            changed = ToolCall(
                name="write_demo",
                arguments={"path": "demo.txt", "text": "changed"},
                external_effect=True,
            )
            kernel.invoke_tool(changed, intent, [receipt.receipt_id])
        except FailClosedError as exc:
            print({"blocked_changed_arguments": str(exc)})


if __name__ == "__main__":
    main()
