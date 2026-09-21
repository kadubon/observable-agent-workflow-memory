from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from observable_agent_workflow_memory.qualified import native
from observable_agent_workflow_memory.qualified.checker import check_view
from observable_agent_workflow_memory.qualified.cli import app
from observable_agent_workflow_memory.qualified.example import context, setup
from observable_agent_workflow_memory.qualified.runtime import ReceiverRuntime
from observable_agent_workflow_memory.qualified.store import append, entries, event, replay
from observable_agent_workflow_memory.qualified.wire import Cost, digest, encoded


@pytest.fixture
def ready(tmp_path: Path) -> Any:
    return setup(tmp_path)


def test_action_id_and_empty_receipt_regressions(ready: Any) -> None:
    kernel, _, _, intent, receipts = ready
    from observable_agent_workflow_memory.core.errors import FailClosedError

    receipt = kernel.storage.get_receipt(receipts[0])
    with pytest.raises(FailClosedError, match="identity"):
        kernel.action_gate.ensure_allowed(
            external_effects=True,
            receipts=[receipt],
            intent=intent.model_copy(update={"resource_caps": {"max_steps": 999}}),
        )
    with pytest.raises(FailClosedError):
        kernel.action_gate.ensure_allowed(
            external_effects=True,
            receipts=[receipt.model_copy(update={"checks": []})],
            intent=intent,
        )


def test_duplicate_reconciliation_and_conflicting_use(ready: Any) -> None:
    _, receiver, q, intent, receipts = ready
    cost = Cost(id="use-cost", stage="use", amount="1")
    receiver.use(
        digest(q),
        q.context.inputs[0],
        identity="use",
        now=4,
        expected=receiver.store.inspect()["revision"],
        intent=intent,
        receipts=receipts,
        cost=cost,
    )
    with receiver.store.readonly() as con:
        old = entries(con)
    retried = event("reconciled", "another-delivery", {"intent": "use"}, 5, old)
    assert replay(old + [retried])["services"] == ["use"]
    with pytest.raises(ValueError, match="conflicting"):
        receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="use",
            now=4,
            expected=receiver.store.inspect()["revision"],
            intent=intent,
            receipts=receipts,
            cost=cost.model_copy(update={"amount": "2"}),
        )


def test_independent_checker_cost_withdrawal_scope(ready: Any) -> None:
    _, receiver, q, _, _ = ready
    view = receiver.retrieve("A", q.context.inputs[0], now=4)["views"][0]
    state = receiver.store.inspect()
    variants = [
        {**state, "costs": {}},
        {**state, "withdrawn": [{"dependency": native.IMPLEMENTATION}]},
        {
            **state,
            "blocks": [
                {
                    "artifact": q.candidate["artifact_digest"],
                    "context": digest(q.context),
                    "input": q.context.inputs[0],
                    "time": 4,
                }
            ],
        },
    ]
    for modified in variants:
        with (
            receiver.store.readonly() as con,
            patch(
                "observable_agent_workflow_memory.qualified.checker.replay", return_value=modified
            ),
            pytest.raises(ValueError),
        ):
            check_view(con, view, q.context, q.context.inputs[0], 4)


def test_projection_receiver_binding_and_failed_source(ready: Any) -> None:
    _, _, q, _, _ = ready
    bad = q.model_copy(deep=True)
    bad.offer["receiver"] = "other"
    with pytest.raises(ValueError, match="context"):
        native.reconstruct(bad, 4)
    source = q.training[0].model_copy(deep=True)
    source.raw = encoded({**source.read(), "output": "bad", "outcome": "failure"})
    source.sha256 = source.producer_digest = native.sha(source.raw)
    request, candidate, _ = native.form([source, q.training[1]], q.context, 2, q.costs[0])
    assert candidate["qualification"] == "unqualified"
    assert request["cost"] == "1"
    assert native.checked(native.operation(source)) is False


def test_guarded_runtime_api_errors(ready: Any) -> None:
    kernel, receiver, q, intent, receipts = ready
    expected = receiver.store.inspect()["revision"]
    nohost = ReceiverRuntime(None, receiver.store.path, [context()])
    with pytest.raises(ValueError):
        nohost.run("x", "A", q.context.inputs[0], now=4)
    with pytest.raises(ValueError):
        nohost.use(
            digest(q),
            q.context.inputs[0],
            identity="u",
            now=4,
            expected=expected,
            intent=intent,
            receipts=receipts,
            cost=Cost(id="u", stage="use", amount="1"),
        )
    with pytest.raises(ValueError):
        receiver.admit(q, now=4, expected="0" * 64)
    q2 = q.model_copy(deep=True)
    q2.context.receiver = "not-registered"
    with pytest.raises(ValueError):
        receiver.admit(q2, now=4, expected=expected)
    with pytest.raises(ValueError):
        receiver.record("admit", "x", {}, now=4, expected=expected)
    with pytest.raises(ValueError):
        receiver.use(
            digest(q),
            "other",
            identity="u",
            now=4,
            expected=expected,
            intent=intent,
            receipts=receipts,
            cost=Cost(id="u", stage="use", amount="1"),
        )
    with patch.object(kernel, "verify_receipt") as verifier:
        verifier.return_value.passed = False
        with pytest.raises(ValueError, match="receipt integrity"):
            receiver.use(
                digest(q),
                q.context.inputs[0],
                identity="u",
                now=4,
                expected=expected,
                intent=intent,
                receipts=receipts,
                cost=Cost(id="u", stage="use", amount="1"),
            )
    receiver.record(
        "withdraw",
        "withdraw",
        {"dependency": native.IMPLEMENTATION, "reason": "test"},
        now=5,
        expected=expected,
    )
    with pytest.raises(ValueError, match="eligibility"):
        receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="u",
            now=5,
            expected=receiver.store.inspect()["revision"],
            intent=intent,
            receipts=receipts,
            cost=Cost(id="u", stage="use", amount="1"),
        )


def test_ro_cli_and_limits(ready: Any, tmp_path: Path) -> None:
    _, receiver, q, _, _ = ready
    policy = tmp_path / "policy.json"
    policy.write_text(encoded([q.context.model_dump()]))
    runner = CliRunner()
    result = runner.invoke(
        app, ["retrieve", str(receiver.store.path), str(policy), "A", q.context.inputs[0], "4"]
    )
    assert result.exit_code == 0, result.exception
    assert json.loads(result.stdout)["views"]

    # Exercise actual resource listing against the source resources awaiting wheel placement.
    class Root:
        def joinpath(self, _: str) -> Path:
            return Path(__file__).resolve().parents[1]

    with patch("observable_agent_workflow_memory.qualified.cli.files", return_value=Root()):
        result = runner.invoke(app, ["resources"])
        assert "003_receiver_events.sql" in result.stdout
    with receiver.store.transaction() as con:
        con.execute(
            "INSERT INTO receiver_events(id,raw_json) VALUES (?,?)", ("oversize", " " * 2_000_001)
        )
    with pytest.raises(ValueError, match="byte limit"):
        receiver.store.inspect()


def test_allegations_do_not_revoke(ready: Any) -> None:
    _, receiver, q, _, _ = ready
    receiver.record(
        "allegation",
        "claim",
        {
            "artifact": q.candidate["artifact_digest"],
            "context": digest(q.context),
            "input": q.context.inputs[0],
            "reason": "untrusted report",
        },
        now=5,
        expected=receiver.store.inspect()["revision"],
    )
    assert receiver.retrieve("A", q.context.inputs[0], now=5)["views"]
    assert receiver.store.inspect()["allegations"]


def test_failed_proposal_costs_and_timeouts(ready: Any) -> None:
    kernel, receiver, q, intent, receipts = ready
    with pytest.raises(native.AttemptError) as error:
        native.propose(
            memory_id=q.memory_id,
            update_id=q.update_id,
            workflow_digest=q.workflow_digest,
            context=q.context,
            training=q.training,
            evaluation=q.evaluation,
            cutoff=2,
            valid_from=50,
            valid_until=100,
            formation_cost=q.costs[0],
        )
    assert len(error.value.payable_costs) == len(q.costs)

    def timeout(args: Any, context: Any) -> Any:
        raise TimeoutError("synthetic bounded timeout")

    kernel.tool_adapter.register("normalize-lines-v1", timeout)
    result = receiver.use(
        digest(q),
        q.context.inputs[0],
        identity="timeout",
        now=4,
        expected=receiver.store.inspect()["revision"],
        intent=intent,
        receipts=receipts,
        cost=Cost(id="timeout", stage="use", amount="1"),
    )
    state = receiver.store.inspect()
    assert not result["service"] and state["outcomes"]["timeout"]["status"] == "timeout"
    assert state["unresolved"] == ["timeout"] and not state["blocks"]


def test_untrusted_retriever_and_weakening(ready: Any) -> None:
    kernel, receiver, q, _, _ = ready
    with patch.object(kernel.retriever, "search", side_effect=AssertionError("untrusted backend")):
        assert receiver.retrieve("A", q.context.inputs[0], now=4)["views"]
    receiver.profiles["A"] = q.context.model_copy(update={"expose": False})
    assert not receiver.retrieve("A", q.context.inputs[0], now=4)["views"]


def test_independent_cost_order_and_limits() -> None:
    a = Cost(id="a", stage="formation", amount="1")
    b = Cost(id="b", stage="verification", amount="1")
    left = [event("cost", "a", a.model_dump(), 1, [])]
    left.append(event("cost", "b", b.model_dump(), 1, left))
    right = [event("cost", "b", b.model_dump(), 1, [])]
    right.append(event("cost", "a", a.model_dump(), 1, right))
    assert replay(left)["costs"] == replay(right)["costs"]
    assert replay(left)["revision"] != replay(right)["revision"]
    with pytest.raises(ValueError, match="count"):
        native.form([], context(), 2, a)


def test_sqlite_fence_during_supported_effect(ready: Any) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import TimeoutError as FutureTimeout
    from threading import Event

    kernel, receiver, q, intent, receipts = ready
    entered, release = Event(), Event()

    def tool(args: Any, context: Any) -> dict[str, str]:
        entered.set()
        assert release.wait(4)
        return {"text": native.normalize(args["text"])}

    kernel.tool_adapter.register("normalize-lines-v1", tool)
    expected = receiver.store.inspect()["revision"]
    with ThreadPoolExecutor(2) as pool:
        use = pool.submit(
            receiver.use,
            digest(q),
            q.context.inputs[0],
            identity="fenced",
            now=4,
            expected=expected,
            intent=intent,
            receipts=receipts,
            cost=Cost(id="fenced", stage="use", amount="1"),
        )
        assert entered.wait(4)

        # A writer cannot cross the execution fence. Once it acquires the lock,
        # it must use the resulting current revision, not an earlier decision.
        def withdraw() -> None:
            with receiver.store.transaction() as con:
                old = entries(con)
                item = event(
                    "withdraw",
                    "concurrent",
                    {"dependency": native.IMPLEMENTATION, "reason": "host"},
                    5,
                    old,
                )
                append(con, [item], replay(old)["revision"])

        pending = pool.submit(withdraw)
        try:
            with pytest.raises(FutureTimeout):
                pending.result(timeout=0.1)
        finally:
            release.set()
        assert use.result()["service"]
        pending.result()
    assert not receiver.retrieve("A", q.context.inputs[0], now=5)["views"]
    assert receiver.store.inspect()["services"] == ["fenced"]
