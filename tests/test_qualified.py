from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from observable_agent_workflow_memory.qualified.checker import check_view
from observable_agent_workflow_memory.qualified.economics import compare
from observable_agent_workflow_memory.qualified.eligibility import decision
from observable_agent_workflow_memory.qualified.example import observe, run, setup
from observable_agent_workflow_memory.qualified.native import (
    IMPLEMENTATION,
    checked,
    normalize,
    propose,
    reconstruct,
)
from observable_agent_workflow_memory.qualified.store import (
    Store,
    append,
    entries,
    event,
    replay,
)
from observable_agent_workflow_memory.qualified.wire import (
    Cost,
    Operation,
    digest,
    encoded,
    loads,
    sha,
)


@pytest.fixture
def ready(tmp_path: Path) -> Any:
    return setup(tmp_path)


def test_installed_example() -> None:
    assert run()["unique_services"] == 1


def test_economic_loss_and_native_checker(ready: Any) -> None:
    _, _, q, _, _ = ready
    result = compare(q, 4)
    assert result["plans"]["all"]["selected"] == ["scratch"]
    assert result["technical_eligibility"]
    assert compare(q, 4, "0")["plans"]["all"]["selected"] == ["reuse"]
    assert not compare(q, 4, limit=1)["plans"]["all"]["complete"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("receiver", "other"),
        ("mission", "other"),
        ("protocol", "other"),
        ("evaluator", "other"),
        ("tool_version", "other"),
        ("clock", "other"),
        ("dependencies", ["0" * 64]),
        ("inputs", ["other"]),
        ("expose", False),
    ],
)
def test_separate_context_mismatches(ready: Any, field: str, value: Any) -> None:
    _, receiver, q, _, _ = ready
    ctx = q.context.model_copy(update={field: value})
    with receiver.store.readonly() as con:
        report = decision(con, q, ctx, q.context.inputs[0], 4, receiver.store.inspect())
    assert report["current_memory_eligibility"] == "blocked"


def test_boundaries_readonly_stale_and_explicit_exposure(ready: Any) -> None:
    kernel, receiver, q, intent, receipts = ready
    path = receiver.store.path
    before = {p.name: p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    assert receiver.retrieve("A", q.context.inputs[0], now=3)["views"]
    assert not receiver.retrieve("A", q.context.inputs[0], now=100)["views"]
    assert before == {p.name: p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    old = receiver.store.inspect()["revision"]
    kernel.run_qualified(
        "normalize", receiver_runtime=receiver, receiver="A", input_text=q.context.inputs[0], now=4
    )
    assert not receiver.store.inspect()["services"]
    with pytest.raises(ValueError, match="stale"):
        receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="stale",
            now=4,
            expected=old,
            intent=intent,
            receipts=receipts,
            cost=Cost(id="use", stage="use", amount="1"),
        )


def test_checked_negative_scoped_refresh_and_cost_retention(ready: Any) -> None:
    kernel, receiver, q, intent, receipts = ready
    kernel.tool_adapter.register("normalize-lines-v1", lambda a, c: {"text": "wrong"})
    outcome = receiver.use(
        digest(q),
        q.context.inputs[0],
        identity="negative",
        now=5,
        expected=receiver.store.inspect()["revision"],
        intent=intent,
        receipts=receipts,
        cost=Cost(id="failure-cost", stage="use", amount="2"),
    )
    assert (
        not outcome["service"] and not receiver.retrieve("A", q.context.inputs[0], now=5)["views"]
    )
    with pytest.raises(ValueError):
        receiver.admit(q, now=6, expected=receiver.store.inspect()["revision"])
    fresh = propose(
        memory_id=q.memory_id,
        update_id=q.update_id,
        workflow_digest=q.workflow_digest,
        context=q.context,
        training=q.training,
        evaluation=[observe(kernel, q.context, q.context.inputs[0], 7, "evaluation", "refresh")],
        cutoff=2,
        valid_from=7,
        valid_until=100,
        formation_cost=q.costs[0],
    )
    receiver.admit(fresh, now=7, expected=receiver.store.inspect()["revision"])
    assert receiver.retrieve("A", q.context.inputs[0], now=7)["views"]
    assert receiver.store.inspect()["costs"]["failure-cost"]["amount"] == "2"


def test_source_mutation_holdout_missing_mapping(ready: Any) -> None:
    _, _, q, _, _ = ready
    forged = q.model_copy(deep=True)
    forged.training[0].raw += " "
    with pytest.raises(ValueError, match="digest"):
        reconstruct(forged, 4)
    forged = q.model_copy(deep=True)
    forged.mapping = {}
    with pytest.raises(ValueError, match="unmapped"):
        reconstruct(forged, 4)
    for split, time in (("evaluation", 1), ("training", 10)):
        forged = q.model_copy(deep=True)
        op = loads(forged.training[0].raw)
        op.update(split=split, time=time)
        source = forged.training[0]
        source.raw = encoded(op)
        source.sha256 = sha(source.raw)
        from observable_agent_workflow_memory.core.canonical import digest_json

        source.producer_digest = digest_json(op)
        with pytest.raises(ValueError):
            reconstruct(forged, 4)


def test_independent_view_forgery_and_revocation(ready: Any) -> None:
    _, receiver, q, _, _ = ready
    view = receiver.retrieve("A", q.context.inputs[0], now=4)["views"][0]
    with receiver.store.readonly() as con:
        check_view(con, view, q.context, q.context.inputs[0], 4)
        with pytest.raises(ValueError):
            check_view(
                con, {**view, "claim": "execute malicious prose"}, q.context, q.context.inputs[0], 4
            )
        with pytest.raises(ValueError):
            check_view(
                con, {**view, "execution_authority": True}, q.context, q.context.inputs[0], 4
            )
    receiver.record(
        "withdraw",
        "withdraw",
        {"dependency": IMPLEMENTATION, "reason": "host"},
        now=5,
        expected=view["snapshot"],
    )
    assert not receiver.retrieve("A", q.context.inputs[0], now=5)["views"]
    with receiver.store.readonly() as con, pytest.raises(ValueError):
        check_view(con, view, q.context, q.context.inputs[0], 5)


def test_action_gate_cannot_be_waived(ready: Any) -> None:
    _, receiver, q, intent, _ = ready
    from observable_agent_workflow_memory.core.errors import FailClosedError

    with pytest.raises(FailClosedError):
        receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="forbidden",
            now=4,
            expected=receiver.store.inspect()["revision"],
            intent=intent,
            receipts=[],
            cost=Cost(id="use", stage="use", amount="1"),
        )
    assert not receiver.store.inspect()["intents"]


def test_transaction_rollback_retry_and_replay(ready: Any) -> None:
    _, receiver, _, _, _ = ready
    old = receiver.store.inspect()
    with pytest.raises(RuntimeError), receiver.store.transaction() as con:
        log = entries(con)
        item = event(
            "cost",
            "rollback",
            Cost(id="rollback", stage="maintenance", amount="2").model_dump(),
            4,
            log,
        )
        append(con, [item], old["revision"])
        raise RuntimeError("synthetic transaction failure")
    assert receiver.store.inspect() == old
    with receiver.store.readonly() as con:
        log = entries(con)
    assert replay(log + [log[-1]]) == replay(log)
    with pytest.raises(ValueError, match="conflicting"):
        replay(log + [log[-1].model_copy(update={"time": 12})])
    with pytest.raises(ValueError, match="parent"):
        replay([log[-1]])
    assert Store(receiver.store.path).inspect() == old
    receiver.store.initialize()
    assert receiver.store.inspect() == old


def test_duplicate_admission(ready: Any) -> None:
    _, receiver, q, _, _ = ready
    before = receiver.store.inspect()
    assert receiver.admit(q, now=4, expected=before["revision"]) == before["revision"]
    assert receiver.store.inspect() == before


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', "NaN", "1.2", "[" * 26 + "0" + "]" * 26])
def test_strict_json(raw: str) -> None:
    with pytest.raises(ValueError):
        loads(raw)


@pytest.mark.parametrize("value", ["-1", "1.0", "01", "1/0", "1" * 82, "NaN"])
def test_quantities(value: str) -> None:
    with pytest.raises((ValueError, ZeroDivisionError)):
        Cost(id="c", stage="formation", amount=value)


@given(st.lists(st.text(alphabet="abc", max_size=5), max_size=8))
@settings(max_examples=30)
def test_independent_normalization_oracle(lines: list[str]) -> None:
    text = "\n".join(lines)
    result = normalize(text)
    op = Operation(
        implementation=IMPLEMENTATION,
        input=text,
        output=result,
        receiver="A",
        context_digest=digest({}),
        time=1,
        split="training",
        outcome="success",
        cost=Cost(id="c", stage="formation", amount="0"),
    )
    assert checked(op)
    assert normalize(result) == result


def test_empty_checkers_security_regression(tmp_path: Path) -> None:
    from observable_agent_workflow_memory.core.errors import FailClosedError
    from observable_agent_workflow_memory.runtime.kernel import AgentKernel

    kernel = AgentKernel.open(tmp_path, plugins={"checkers": []})
    kernel.observe("note", {"text": "not proof"}, run_id="x")
    memory = kernel.propose_memory("x")
    with pytest.raises(FailClosedError, match="nonempty"):
        kernel.verify(memory.memory_id)
