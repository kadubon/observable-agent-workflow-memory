"""Plugin discovery helpers."""

from __future__ import annotations

from importlib.metadata import EntryPoint, entry_points
from typing import Any

PLUGIN_GROUPS = [
    "oawm.llm_providers",
    "oawm.storage_backends",
    "oawm.retrievers",
    "oawm.checkers",
    "oawm.proposers",
    "oawm.tool_adapters",
    "oawm.receipt_verifiers",
]


def list_entry_points() -> dict[str, list[EntryPoint]]:
    eps = entry_points()
    return {group: list(eps.select(group=group)) for group in PLUGIN_GROUPS}


def load_entry_point(group: str, name: str) -> Any:
    eps = entry_points().select(group=group, name=name)
    matches = list(eps)
    if not matches:
        msg = f"plugin not found: {group}:{name}"
        raise LookupError(msg)
    return matches[0].load()
