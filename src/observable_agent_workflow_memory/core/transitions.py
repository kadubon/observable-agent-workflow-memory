"""Lane transition rules."""

from __future__ import annotations

from observable_agent_workflow_memory.core.errors import TransitionError
from observable_agent_workflow_memory.core.models import Lane, MemoryRecord

ALLOWED_TRANSITIONS: dict[Lane, set[Lane]] = {
    Lane.RAW: {Lane.CANDIDATE, Lane.CONTRADICTION, Lane.TOMBSTONE},
    Lane.CANDIDATE: {Lane.SHADOW, Lane.QUARANTINE, Lane.CONTRADICTION, Lane.TOMBSTONE},
    Lane.SHADOW: {Lane.CERTIFIED, Lane.QUARANTINE, Lane.CONTRADICTION, Lane.TOMBSTONE},
    Lane.CERTIFIED: {Lane.SUPERSEDED, Lane.CONTRADICTION, Lane.TOMBSTONE},
    Lane.SUPERSEDED: {Lane.CONTRADICTION, Lane.TOMBSTONE},
    Lane.QUARANTINE: {Lane.CANDIDATE, Lane.TOMBSTONE},
    Lane.CONTRADICTION: {Lane.CANDIDATE, Lane.TOMBSTONE},
    Lane.TOMBSTONE: set(),
}


def assert_transition_allowed(source: Lane, target: Lane) -> None:
    if source == target:
        return
    if target not in ALLOWED_TRANSITIONS[source]:
        msg = f"invalid memory lane transition: {source.value} -> {target.value}"
        raise TransitionError(msg)


def move_memory(record: MemoryRecord, target: Lane, *, reason: str = "") -> MemoryRecord:
    assert_transition_allowed(record.lane, target)
    return record.moved(target, reason=reason)


def admissible_lanes_for_mode(mode: str) -> list[Lane]:
    if mode == "admissible":
        return [Lane.CERTIFIED]
    if mode == "raw":
        return [Lane.RAW]
    if mode == "candidate":
        return [Lane.CANDIDATE, Lane.SHADOW]
    if mode == "audit":
        return [
            Lane.RAW,
            Lane.CANDIDATE,
            Lane.SHADOW,
            Lane.CERTIFIED,
            Lane.SUPERSEDED,
            Lane.QUARANTINE,
            Lane.TOMBSTONE,
            Lane.CONTRADICTION,
        ]
    msg = f"unknown retrieval mode: {mode}"
    raise TransitionError(msg)
