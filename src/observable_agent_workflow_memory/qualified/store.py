"""Single-host transactional append log beside unchanged legacy tables."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .wire import Cost, Entry, Qualification, digest, encoded, loads

EMPTY = digest([])


def replay(entries: list[Entry]) -> dict[str, Any]:
    if len(entries) > 256:
        raise ValueError("journal event limit")
    state: dict[str, Any] = {
        "qualifications": {},
        "costs": {},
        "blocks": [],
        "withdrawn": [],
        "intents": {},
        "attempts": {},
        "outcomes": {},
        "checked": {},
        "services": [],
        "exposures": [],
        "allegations": [],
    }
    unique: list[dict[str, Any]] = []
    ids: dict[str, str] = {}
    for entry in entries:
        entry = Entry.model_validate(entry.model_dump())
        value = digest(entry)
        if entry.id in ids:
            if ids[entry.id] != value:
                raise ValueError("conflicting event id")
            continue
        if entry.previous != digest(unique):
            raise ValueError("missing parent or stale revision")
        ids[entry.id] = value
        data = entry.data
        kind = entry.kind
        if kind == "cost":
            cost = Cost.model_validate(data)
            if cost.id in state["costs"] and state["costs"][cost.id] != data:
                raise ValueError("conflicting physical cost")
            state["costs"][cost.id] = data
        elif kind == "admit":
            q = Qualification.model_validate(data)
            if any(state["costs"].get(c.id) != c.model_dump() for c in q.costs):
                raise ValueError("unpaid qualification obligations")
            state["qualifications"][digest(q)] = data
        elif kind in {"invalidate", "withdraw", "allegation"}:
            required = (
                {"dependency", "reason"}
                if kind == "withdraw"
                else {"artifact", "context", "input", "reason"}
            )
            if set(data) != required or not all(isinstance(v, str) for v in data.values()):
                raise ValueError("invalid blocking event")
            key = (
                "withdrawn"
                if kind == "withdraw"
                else "allegations"
                if kind == "allegation"
                else "blocks"
            )
            state[key].append({**data, "time": entry.time, "event": entry.id})
        elif kind == "exposure":
            if (
                set(data) != {"qualification", "input"}
                or data["qualification"] not in state["qualifications"]
            ):
                raise ValueError("unbound exposure")
            state["exposures"].append(data)
        elif kind == "intent":
            if (
                set(data) != {"qualification", "input", "action", "cost", "snapshot"}
                or data["qualification"] not in state["qualifications"]
                or data["cost"] not in state["costs"]
            ):
                raise ValueError("unbound use intent or cost")
            state["intents"][entry.id] = data
        elif kind == "attempt":
            if (
                set(data) != {"intent"}
                or data["intent"] not in state["intents"]
                or data["intent"] in state["attempts"]
            ):
                raise ValueError("missing or repeated attempt")
            state["attempts"][data["intent"]] = entry.id
        elif kind == "outcome":
            if (
                set(data) != {"intent", "output", "status"}
                or data["intent"] not in state["attempts"]
                or data["intent"] in state["outcomes"]
                or data["status"] not in {"received", "timeout", "unknown"}
            ):
                raise ValueError("unbound outcome")
            state["outcomes"][data["intent"]] = data
        elif kind == "checked":
            if (
                set(data) != {"intent", "checker"}
                or data["checker"] != "normalize-checker-v1"
                or data["intent"] not in state["outcomes"]
            ):
                raise ValueError("unbound outcome check")
            outcome = state["outcomes"][data["intent"]]
            intent = state["intents"][data["intent"]]
            from .native import IMPLEMENTATION, checked
            from .wire import Operation

            op = Operation(
                implementation=IMPLEMENTATION,
                input=intent["input"],
                output=outcome["output"],
                receiver="local",
                context_digest=digest({}),
                time=entry.time,
                split="evaluation",
                outcome="success" if outcome["status"] == "received" else "unknown",
                cost=Cost.model_validate(state["costs"][intent["cost"]]),
            )
            state["checked"][data["intent"]] = checked(op)
            if outcome["status"] == "received" and not checked(op):
                q = Qualification.model_validate(state["qualifications"][intent["qualification"]])
                state["blocks"].append(
                    {
                        "artifact": q.candidate["artifact_digest"],
                        "context": digest(q.context),
                        "input": intent["input"],
                        "time": entry.time,
                        "event": entry.id,
                        "reason": "checked-negative",
                    }
                )
        elif kind == "reconciled":
            if set(data) != {"intent"} or data["intent"] not in state["checked"]:
                raise ValueError("unchecked reconciliation")
            if state["checked"][data["intent"]] and data["intent"] not in state["services"]:
                state["services"].append(data["intent"])
        else:
            raise ValueError("unsupported_correction: append new evidence; original records remain")
        unique.append(entry.model_dump())
    state["revision"] = digest(unique)
    state["unresolved"] = sorted(
        identity
        for identity in state["intents"]
        if identity not in state["checked"] or state["outcomes"][identity]["status"] != "received"
    )
    return state


def entries(con: sqlite3.Connection) -> list[Entry]:
    size = con.execute("SELECT COALESCE(SUM(length(raw_json)),0) FROM receiver_events").fetchone()[
        0
    ]
    if size > 2_000_000:
        raise ValueError("journal byte limit")
    rows = con.execute("SELECT raw_json FROM receiver_events ORDER BY seq LIMIT 257").fetchall()
    if len(rows) > 256:
        raise ValueError("journal event limit")
    return [Entry.model_validate(loads(row[0])) for row in rows]


class Store:
    def __init__(self, path: Path):
        self.path = path.resolve()

    def initialize(self) -> None:
        if not self.path.is_file():
            raise ValueError("initialize legacy OAWM first")
        with self.transaction() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS receiver_events "
                "(seq INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE, raw_json TEXT NOT NULL)"
            )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path, timeout=5)
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    @contextmanager
    def readonly(self) -> Iterator[sqlite3.Connection]:
        if not self.path.is_file():
            raise ValueError("state does not exist")
        wal = Path(str(self.path) + "-wal")
        if wal.exists() and wal.stat().st_size:
            raise ValueError(
                "active WAL: use a transaction snapshot or checkpoint before read-only inspection"
            )
        con = sqlite3.connect(self.path.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            yield con
        finally:
            con.close()

    def inspect(self) -> dict[str, Any]:
        with self.readonly() as con:
            return replay(entries(con))

    def append(self, batch: list[Entry], expected: str) -> str:
        with self.transaction() as con:
            return append(con, batch, expected)


def append(con: sqlite3.Connection, batch: list[Entry], expected: str) -> str:
    old = entries(con)
    current = replay(old)
    if current["revision"] != expected:
        raise ValueError("stale expected revision")
    result = replay(old + batch)
    for item in batch:
        existing = con.execute(
            "SELECT raw_json FROM receiver_events WHERE id=?", (item.id,)
        ).fetchone()
        if existing is None:
            con.execute(
                "INSERT INTO receiver_events(id,raw_json) VALUES (?,?)", (item.id, encoded(item))
            )
    return str(result["revision"])


def event(kind: str, identity: str, data: dict[str, Any], time: int, old: list[Entry]) -> Entry:
    return Entry.model_validate(
        dict(id=identity, previous=replay(old)["revision"], time=time, kind=kind, data=data)
    )
