from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from observable_agent_workflow_memory.qualified import native
from observable_agent_workflow_memory.qualified.cli import app
from observable_agent_workflow_memory.qualified.eligibility import decision, row
from observable_agent_workflow_memory.qualified.example import context, setup
from observable_agent_workflow_memory.qualified.runtime import ReceiverRuntime
from observable_agent_workflow_memory.qualified.store import EMPTY, Store, event, replay
from observable_agent_workflow_memory.qualified.wire import (
    Context,
    Cost,
    Entry,
    Source,
    digest,
    encoded,
    loads,
    sha,
)


@pytest.fixture
def ready(tmp_path: Path) -> Any:
    return setup(tmp_path)


def test_cli_paths(ready: Any, tmp_path: Path) -> None:
    _, receiver, q, _, _ = ready
    path = tmp_path / "qualification.json"
    path.write_text(encoded(q))
    runner = CliRunner()
    for args in (
        ["inspect", str(receiver.store.path)],
        ["check", str(path), "4"],
        ["export", str(path)],
        ["example"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output + str(result.exception)
    # Resource layout is installed by wheel force-include; avoid inventing checkout resources.
    from importlib.resources import files

    with patch(
        "observable_agent_workflow_memory.qualified.cli.files",
        return_value=files("observable_agent_workflow_memory").parent.parent,
    ):
        pass


@pytest.mark.parametrize(
    "kind,data",
    [
        ("exposure", {}),
        ("intent", {}),
        ("attempt", {}),
        ("outcome", {}),
        ("checked", {}),
        ("reconciled", {}),
        ("withdraw", {}),
        ("invalidate", {}),
        ("correction", {}),
    ],
)
def test_unbound_or_unsupported_events(kind: str, data: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        replay([event(kind, "bad", data, 1, [])])


def test_cost_id_and_obligation_checks(ready: Any) -> None:
    _, receiver, q, _, _ = ready
    cost = Cost(id="c", stage="formation", amount="1")
    first = event("cost", "first", cost.model_dump(), 1, [])
    second = event(
        "cost", "second", cost.model_copy(update={"amount": "2"}).model_dump(), 2, [first]
    )
    with pytest.raises(ValueError, match="physical"):
        replay([first, second])
    with pytest.raises(ValueError, match="unpaid"):
        replay([event("admit", "q", q.model_dump(), 3, [])])
    state = receiver.store.inspect()
    state["costs"] = {}
    with receiver.store.readonly() as con:
        assert (
            decision(con, q, q.context, q.context.inputs[0], 4, state)["current_memory_eligibility"]
            == "blocked"
        )


@pytest.mark.parametrize(
    "change",
    [
        "context",
        "scope",
        "implementation",
        "validity",
        "domain",
        "evidence",
        "cost",
        "semantics",
        "producer",
        "overlap",
    ],
)
def test_native_reconstruction_guards(ready: Any, change: str) -> None:
    _, _, q, _, _ = ready
    q = q.model_copy(deep=True)
    if change == "context":
        q.context.evaluator = "unregistered"
    elif change == "scope":
        q.cutoff = 1
    elif change == "implementation":
        q.formation["library"][0]["implementation"] = "0" * 64
    elif change == "validity":
        q.valid_until = 90
    elif change == "domain":
        q.offer["inputs"] = ["0" * 64]
    elif change == "evidence":
        q.evaluation[0].raw = encoded({**q.evaluation[0].read(), "receiver": "B"})
        q.evaluation[0].sha256 = sha(q.evaluation[0].raw)
        q.evaluation[0].producer_digest = sha(q.evaluation[0].raw)
    elif change == "cost":
        q.costs = q.costs[:-1]
    elif change == "semantics":
        q.offer["postconditions"] = ["universal-correctness"]
    elif change == "producer":
        q.training[0].producer_digest = "0" * 64
    elif change == "overlap":
        q.evaluation[0].event_id = q.training[0].event_id
    with pytest.raises(ValueError):
        native.reconstruct(q, 4)


def test_projection_extractor_rejects_holdout(ready: Any) -> None:
    _, _, q, _, _ = ready
    source = q.training[0].model_copy(deep=True)
    source.raw = encoded({**source.read(), "split": "evaluation"})
    source.sha256 = source.producer_digest = sha(source.raw)
    with pytest.raises(ValueError, match="holdout"):
        native.form([source, q.training[1]], q.context, 2, q.costs[0])


@pytest.mark.parametrize(
    "table,key,mutation",
    [
        ("memory_records", "memory_id", {"lane": "tombstone"}),
        ("memory_records", "memory_id", {"update_id": "upd_wrong"}),
        ("promotion_receipts", "receipt_id", {"checks": []}),
        ("promotion_receipts", "receipt_id", {"receipt_digest": "0" * 64}),
        ("workflow_contracts", "contract_id", {"source_update_id": "upd_wrong"}),
    ],
)
def test_authoritative_legacy_bindings(
    ready: Any, table: str, key: str, mutation: dict[str, Any]
) -> None:
    _, receiver, q, _, _ = ready
    with receiver.store.transaction() as con:
        memory = row(con, "memory_records", "memory_id", q.memory_id)
        identity = (
            q.memory_id
            if table == "memory_records"
            else memory["receipt_id"]
            if table == "promotion_receipts"
            else memory["workflow_contract_id"]
        )
        raw = row(con, table, key, identity)
        raw.update(mutation)
        con.execute(f"UPDATE {table} SET raw_json=? WHERE {key}=?", (json.dumps(raw), identity))
    assert not receiver.retrieve("A", q.context.inputs[0], now=4)["views"]


def test_source_corruption_and_unmapped_source(ready: Any) -> None:
    _, receiver, q, _, _ = ready
    with receiver.store.transaction() as con:
        original = row(con, "events", "event_id", q.training[0].event_id)
        original["payload"]["raw"] = "{}"
        con.execute(
            "UPDATE events SET raw_json=? WHERE event_id=?",
            (json.dumps(original), q.training[0].event_id),
        )
    assert not receiver.retrieve("A", q.context.inputs[0], now=4)["views"]


def test_parser_limits_and_policy_shapes(tmp_path: Path) -> None:
    for value in [
        '"' + "a" * 2_000_000 + '"',
        "[" + "0," * 50000 + "0]",
        "[" * 1100 + "0" + "]" * 1100,
    ]:
        with pytest.raises(ValueError):
            loads(value)
    with pytest.raises(ValueError):
        native.normalize("x" * 4097)
    with pytest.raises(ValueError):
        Context.model_validate({**context().model_dump(), "inputs": ["x", "x"]})
    with pytest.raises(ValueError):
        Context.model_validate({**context().model_dump(), "checks": []})
    source = Source(event_id="e", raw="[]", sha256=sha("[]"), producer_digest=sha("[]"))
    with pytest.raises(ValueError):
        source.read()
    with pytest.raises(ValueError):
        Store(tmp_path / "absent.sqlite").initialize()
    with pytest.raises(ValueError):
        Store(tmp_path / "absent.sqlite").inspect()
    assert not (tmp_path / "absent.sqlite").exists()
    with pytest.raises(ValueError):
        replay([Entry(id="x", previous=EMPTY, time=1, kind="cost", data={})] * 257)


def test_optional_dependencies_and_manifest_integrity() -> None:
    with (
        patch.object(native, "version", side_effect=PackageNotFoundError),
        pytest.raises(ValueError, match="optional_dependency"),
    ):
        native.runtime("alt_foundry_kernel.reuse.formation")
    with (
        patch.object(native, "version", return_value="999"),
        pytest.raises(ValueError, match="version"),
    ):
        native.runtime("alt_foundry_kernel.reuse.formation")
    with pytest.raises(ValueError):
        native.pinned("../../secret")


def test_registry_time_and_readonly_wal(ready: Any) -> None:
    kernel, receiver, q, _, _ = ready
    with pytest.raises(ValueError):
        ReceiverRuntime(kernel, receiver.store.path, [context(), context()])
    with pytest.raises(ValueError):
        receiver.retrieve("unregistered", "x", now=4)
    with receiver.store.readonly() as con:
        with pytest.raises(ValueError):
            decision(con, q, q.context, q.context.inputs[0], True, receiver.store.inspect())
        with pytest.raises(ValueError):
            row(con, "bad", "bad", "bad")
        with pytest.raises(ValueError):
            row(con, "memory_records", "memory_id", "bad")
    wal = Path(str(receiver.store.path) + "-wal")
    wal.write_bytes(b"active")
    with pytest.raises(ValueError, match="WAL"):
        receiver.store.inspect()
    wal.unlink()


def test_failure_transaction_and_unknown_effect(ready: Any) -> None:
    kernel, receiver, q, intent, receipts = ready
    original = receiver.store.inspect()
    with (
        patch.object(kernel, "invoke_tool", side_effect=RuntimeError("crash")),
        pytest.raises(RuntimeError),
    ):
        receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="crashed",
            now=4,
            expected=original["revision"],
            intent=intent,
            receipts=receipts,
            cost=Cost(id="crash-cost", stage="use", amount="1"),
        )
    state = receiver.store.inspect()
    assert "crashed" in state["unresolved"] and not state["services"]
    assert "crash-cost" in state["costs"]
    with pytest.raises(ValueError, match="unresolved"):
        receiver.use(
            digest(q),
            q.context.inputs[0],
            identity="retry-renamed",
            now=4,
            expected=state["revision"],
            intent=intent,
            receipts=receipts,
            cost=Cost(id="second", stage="use", amount="1"),
        )
