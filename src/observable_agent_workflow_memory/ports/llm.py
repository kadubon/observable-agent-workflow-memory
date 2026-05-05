"""LLM provider port."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class LLMMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str


class LLMResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    model: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class LLMProvider(Protocol):
    provider_name: str

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> LLMResult:
        """Return a model completion."""

