"""Consumer-side checker of an eligible view, independent of retrieval/decision code."""

from __future__ import annotations

import sqlite3
from typing import Any

from .eligibility import promotion
from .native import reconstruct
from .store import entries, replay
from .wire import Context, Qualification, digest


def check_view(
    con: sqlite3.Connection, view: dict[str, Any], context: Context, input_text: str, now: int
) -> None:
    state = replay(entries(con))
    q = Qualification.model_validate(state["qualifications"][view["qualification"]])
    if (
        view["snapshot"] != state["revision"]
        or q.context != context
        or not context.expose
        or input_text not in context.inputs
        or not q.valid_from <= now < q.valid_until
        or view["memory_id"] != q.memory_id
        or view["update_id"] != q.update_id
        or view["workflow_digest"] != q.workflow_digest
        or view["context_digest"] != digest(context)
        or view["expiry"] != q.valid_until
        or view["execution_authority"] is not None
        or view["source_authentication"] is not None
        or view["current_memory_eligibility"] != "eligible"
    ):
        raise ValueError("view bindings or scope rejected")
    if any(state["costs"].get(c.id) != c.model_dump() for c in q.costs):
        raise ValueError("unpaid view costs")
    if {item["dependency"] for item in state["withdrawn"]} & set(context.dependencies):
        raise ValueError("withdrawn dependency")
    for block in state["blocks"]:
        if (block["artifact"], block["context"], block["input"]) == (
            q.candidate["artifact_digest"],
            digest(context),
            input_text,
        ) and block["time"] >= q.valid_from:
            raise ValueError("scoped invalidation")
    memory = promotion(con, q)
    if view["claim"] != memory.claim:
        raise ValueError("untrusted retriever content")
    reconstruct(q, now)
