from __future__ import annotations

import pytest

from observable_agent_workflow_memory.core.canonical import canonical_json, digest_json
from observable_agent_workflow_memory.core.errors import FailClosedError, TransitionError
from observable_agent_workflow_memory.core.jsonio import loads_strict_json
from observable_agent_workflow_memory.core.models import Event, Lane, MemoryRecord
from observable_agent_workflow_memory.core.transitions import (
    admissible_lanes_for_mode,
    assert_transition_allowed,
)


def test_canonical_digest_is_order_independent() -> None:
    left = {"b": 2, "a": [3, 1]}
    right = {"a": [3, 1], "b": 2}

    assert digest_json(left) == digest_json(right)


def test_canonical_json_rejects_non_finite_float() -> None:
    with pytest.raises(ValueError):
        canonical_json({"bad": float("nan")})


def test_event_ids_do_not_collide_for_identical_payloads() -> None:
    first = Event.create(kind="note", payload={"text": "same"}, run_id="demo")
    second = Event.create(kind="note", payload={"text": "same"}, run_id="demo")

    assert first.event_id != second.event_id
    assert first.event_nonce != second.event_nonce
    assert first.payload_digest == second.payload_digest


def test_invalid_lane_transition_is_rejected() -> None:
    with pytest.raises(TransitionError):
        assert_transition_allowed(Lane.RAW, Lane.CERTIFIED)

    with pytest.raises(TransitionError):
        assert_transition_allowed(Lane.CANDIDATE, Lane.CERTIFIED)


def test_admissible_mode_only_returns_certified_lane() -> None:
    assert admissible_lanes_for_mode("admissible") == [Lane.CERTIFIED]


def test_memory_record_requires_claim() -> None:
    with pytest.raises(ValueError):
        MemoryRecord.create(lane=Lane.RAW, claim="", source_event_ids=["evt_x"])


def test_memory_record_update_id_is_content_bound_and_lane_move_preserves() -> None:
    record = MemoryRecord.create(
        lane=Lane.CANDIDATE,
        claim="content-bound memory",
        source_event_ids=["evt_x"],
        metadata={"resource_caps": {"max_steps": 2}},
    )
    moved = record.moved(Lane.SHADOW, reason="verified")
    changed = MemoryRecord.create(
        lane=Lane.CANDIDATE,
        claim="content-bound memory",
        source_event_ids=["evt_x"],
        metadata={"resource_caps": {"max_steps": 3}},
    )

    assert record.update_id.startswith("upd_")
    assert moved.update_id == record.update_id
    assert changed.update_id != record.update_id


def test_strict_json_loader_rejects_duplicate_keys_and_non_finite_numbers() -> None:
    with pytest.raises(FailClosedError):
        loads_strict_json('{"a": 1, "a": 2}')
    with pytest.raises(FailClosedError):
        loads_strict_json('{"a": NaN}')
