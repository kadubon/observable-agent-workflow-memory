"""Local in-process tool adapter."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from observable_agent_workflow_memory.core.errors import FailClosedError
from observable_agent_workflow_memory.ports.tools import ToolAdapter, ToolCall, ToolResult

ToolFn = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class LocalToolAdapter(ToolAdapter):
    adapter_name = "local"

    def __init__(self) -> None:
        self._tools: dict[str, ToolFn] = {}
        self._gate_token = uuid.uuid4().hex

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = fn

    def authorized_context(self, context: dict[str, Any]) -> dict[str, Any]:
        data = dict(context)
        data["_oawm_gate_token"] = self._gate_token
        return data

    def invoke(self, call: ToolCall, *, context: dict[str, Any]) -> ToolResult:
        if call.external_effect and context.get("_oawm_gate_token") != self._gate_token:
            raise FailClosedError("external-effect tool call blocked by ActionGate")
        fn = self._tools.get(call.name)
        if fn is None:
            return ToolResult(call_name=call.name, ok=False, error=f"unknown tool: {call.name}")
        try:
            return ToolResult(call_name=call.name, ok=True, output=fn(call.arguments, context))
        except Exception as exc:  # Adapter boundary preserves error as data.
            return ToolResult(call_name=call.name, ok=False, error=f"{type(exc).__name__}: {exc}")


def create_tool_adapter() -> LocalToolAdapter:
    return LocalToolAdapter()
