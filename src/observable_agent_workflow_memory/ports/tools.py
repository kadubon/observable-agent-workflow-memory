"""Tool adapter port."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    external_effect: bool = False


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_name: str
    ok: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str = ""


class ToolAdapter(Protocol):
    adapter_name: str

    def invoke(self, call: ToolCall, *, context: dict[str, Any]) -> ToolResult:
        """Invoke a tool call."""

