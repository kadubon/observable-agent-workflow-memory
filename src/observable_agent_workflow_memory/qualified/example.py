"""Disposable deterministic software demonstration; no empirical acceleration claim."""

from __future__ import annotations

import socket
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

from observable_agent_workflow_memory.adapters.local_tools import LocalToolAdapter
from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.models import ActionIntent
from observable_agent_workflow_memory.runtime.kernel import AgentKernel

from .checker import check_view
from .economics import compare
from .native import IMPLEMENTATION, ccr_proposal, normalize, propose
from .runtime import ReceiverRuntime
from .wire import Context, Cost, Operation, Qualification, Source, digest, encoded, sha


def context(receiver: str = "A") -> Context:
    return Context(
        workspace="synthetic-study",
        receiver=receiver,
        mission="normalize-mission",
        task_family="normalize-text",
        context="local-context",
        inputs=["b\na\nb"],
        clock="host-tick",
        dependencies=[IMPLEMENTATION],
        checks=["normalize-checker-v1"],
        expose=True,
    )


def observe(
    kernel: AgentKernel, ctx: Context, text: str, time: int, split: str, identity: str
) -> Source:
    op = Operation.model_validate(
        dict(
            implementation=IMPLEMENTATION,
            input=text,
            output=normalize(text),
            receiver=ctx.receiver,
            context_digest=digest(ctx),
            time=time,
            split=split,
            outcome="success",
            cost=Cost(
                id=identity,
                stage="formation" if split == "training" else "verification",
                amount="1",
            ).model_dump(),
        )
    )
    raw = encoded(op)
    event = kernel.observe(
        "registered_operation",
        {"raw": raw},
        run_id="training" if split == "training" else identity,
        index_as_raw=False,
    )
    return Source(
        event_id=event.event_id, producer_digest=digest_json(op), raw=raw, sha256=sha(raw)
    )


def setup(
    root: Path,
) -> tuple[AgentKernel, ReceiverRuntime, Qualification, ActionIntent, list[str]]:
    tools = LocalToolAdapter()

    def execute(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
        value = normalize(arguments["text"])
        (root / "result.txt").write_text(value, encoding="utf-8")
        return {"text": (root / "result.txt").read_text(encoding="utf-8")}

    tools.register("normalize-lines-v1", execute)
    kernel = AgentKernel.open(root, plugins={"tool_adapter": tools})
    ctx = context()
    training = [
        observe(kernel, ctx, text, i, "training", f"train-{i}")
        for i, text in enumerate(["z\na", "c\nb\nc"], 1)
    ]
    memory = kernel.propose_memory(
        "training", tools=["normalize-lines-v1"], resource_caps={"max_steps": 4}
    )
    intent = ActionIntent.create(
        tool_name="normalize-lines-v1",
        effect_class="local-external",
        arguments={"text": ctx.inputs[0]},
        resource_caps={"max_steps": 4},
    )
    receipt = kernel.verify(memory.memory_id, action_intent=intent)
    if receipt.result != "passed":
        raise ValueError("legacy promotion failed")
    memory = kernel.promote(memory.memory_id)
    evaluation = [observe(kernel, ctx, ctx.inputs[0], 3, "evaluation", "check-A")]
    q = propose(
        memory_id=memory.memory_id,
        update_id=memory.update_id,
        workflow_digest=memory.content_digest(),
        context=ctx,
        training=training,
        evaluation=evaluation,
        cutoff=2,
        valid_from=3,
        valid_until=100,
        formation_cost=Cost(id="formation", stage="formation", amount="1"),
    )
    receiver = ReceiverRuntime(kernel, root / "oawm.sqlite", [ctx, context("B")])
    receiver.store.initialize()
    receiver.admit(q, now=3, expected=receiver.store.inspect()["revision"])
    return kernel, receiver, q, intent, [receipt.receipt_id]


def run() -> dict[str, Any]:
    def denied(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("runtime sockets blocked")

    with (
        patch.object(socket.socket, "connect", denied),
        patch.object(socket, "create_connection", denied),
        tempfile.TemporaryDirectory(prefix="oawm-example-") as directory,
    ):
        root = Path(directory)
        kernel, receiver, q, intent, receipts = setup(root)
        a = receiver.retrieve("A", q.context.inputs[0], now=4)
        b = receiver.retrieve("B", q.context.inputs[0], now=4)
        assert a["views"] and not b["views"]
        economic = compare(q, 4)
        assert economic["plans"]["all"]["selected"] == ["scratch"]
        legacy_count = len(kernel.retrieve("", limit=8))
        empty_kernel = AgentKernel.open(root / "no-memory")
        no_memory_count = len(empty_kernel.retrieve("", limit=8))
        with receiver.store.readonly() as con:
            check_view(con, a["views"][0], q.context, q.context.inputs[0], 4)
        kernel.run_qualified(
            "normalize",
            receiver_runtime=receiver,
            receiver="A",
            input_text=q.context.inputs[0],
            now=4,
        )
        assert receiver.store.inspect()["services"] == []
        result = receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="use-1",
            now=5,
            expected=receiver.store.inspect()["revision"],
            intent=intent,
            receipts=receipts,
            cost=Cost(id="use-cost", stage="use", amount="1"),
        )
        assert result["service"] and (root / "result.txt").read_text() == "a\nb"
        duplicate = receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="use-1",
            now=5,
            expected=receiver.store.inspect()["revision"],
            intent=intent,
            receipts=receipts,
            cost=Cost(id="use-cost", stage="use", amount="1"),
        )
        assert duplicate["status"] == "duplicate" and len(receiver.store.inspect()["services"]) == 1
        # Deliberately faulty host implementation in this disposable synthetic
        # test: actual file bytes, not an imported "failed" or "passed" flag.
        original_tools = kernel.tool_adapter
        faulty_tools = LocalToolAdapter()

        def faulty(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
            (root / "negative.txt").write_text(arguments["text"] + "\nwrong", encoding="utf-8")
            return {"text": (root / "negative.txt").read_text(encoding="utf-8")}

        faulty_tools.register("normalize-lines-v1", faulty)
        kernel.tool_adapter = faulty_tools
        negative = receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="negative-use",
            now=6,
            expected=receiver.store.inspect()["revision"],
            intent=intent,
            receipts=receipts,
            cost=Cost(id="negative-use-cost", stage="use", amount="1"),
        )
        assert not negative["service"]
        assert not receiver.retrieve("A", q.context.inputs[0], now=6)["views"]
        kernel.tool_adapter = original_tools
        refreshed = propose(
            memory_id=q.memory_id,
            update_id=q.update_id,
            workflow_digest=q.workflow_digest,
            context=q.context,
            training=q.training,
            evaluation=[
                observe(kernel, q.context, q.context.inputs[0], 7, "evaluation", "refresh-check")
            ],
            cutoff=2,
            valid_from=7,
            valid_until=100,
            formation_cost=q.costs[0],
        )
        receiver.admit(refreshed, now=7, expected=receiver.store.inspect()["revision"])
        assert receiver.retrieve("A", q.context.inputs[0], now=7)["views"]
        ctx_b = context("B")
        bq = propose(
            memory_id=q.memory_id,
            update_id=q.update_id,
            workflow_digest=q.workflow_digest,
            context=ctx_b,
            training=q.training,
            evaluation=[observe(kernel, ctx_b, ctx_b.inputs[0], 8, "evaluation", "check-B")],
            cutoff=2,
            valid_from=8,
            valid_until=100,
            formation_cost=q.costs[0],
        )
        receiver.admit(bq, now=8, expected=receiver.store.inspect()["revision"])
        assert receiver.retrieve("B", ctx_b.inputs[0], now=8)["views"]
        handoff = ccr_proposal(refreshed)
        receiver.record(
            "withdraw",
            "withdraw-primitive",
            {"dependency": IMPLEMENTATION, "reason": "host withdrawal"},
            now=9,
            expected=receiver.store.inspect()["revision"],
        )
        assert not receiver.retrieve("A", q.context.inputs[0], now=9)["views"]
        assert not receiver.retrieve("B", q.context.inputs[0], now=9)["views"]
        state = receiver.store.inspect()
        return {
            "version": "oawm-example-v1",
            "synthetic": True,
            "receiver_A_initial": "eligible",
            "receiver_B_initial": "blocked",
            "receiver_B_after_qualification": "eligible",
            "refresh": "restored",
            "withdrawal": "both-blocked",
            "unique_services": len(state["services"]),
            "checked_negative_execution": True,
            "finite_exposure_comparison": {
                "no_memory": no_memory_count,
                "legacy": legacy_count,
                "qualified_A": len(a["views"]),
                "qualified_B_initial": len(b["views"]),
            },
            "costed_ALT_selected": economic["plans"]["all"]["selected"],
            "costs": state["costs"],
            "context_exposure_is_service": False,
            "native_CCR": handoff["native_task"]["schema_version"],
            "host_admission_required": True,
            "runtime_network": "blocked",
            "execution_authority": None,
            "empirical_acceleration": None,
        }


if __name__ == "__main__":
    print(encoded(run()))
