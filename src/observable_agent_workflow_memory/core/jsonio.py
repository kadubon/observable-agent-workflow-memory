"""Strict JSON loading for observable event ingestion."""

from __future__ import annotations

import json
from typing import Any

from observable_agent_workflow_memory.core.errors import FailClosedError


def loads_strict_json(text: str) -> Any:
    """Load JSON while rejecting duplicate keys and non-finite numbers."""

    def reject_constant(value: str) -> None:
        msg = f"non-finite JSON number is not allowed: {value}"
        raise FailClosedError(msg)

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                msg = f"duplicate JSON key is not allowed: {key}"
                raise FailClosedError(msg)
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        msg = f"invalid JSON: {exc.msg}"
        raise FailClosedError(msg) from exc
