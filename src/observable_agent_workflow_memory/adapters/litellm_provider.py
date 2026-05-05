"""LiteLLM provider adapter."""

from __future__ import annotations

import importlib
from typing import Any

from observable_agent_workflow_memory.ports.llm import LLMMessage, LLMResult


class LiteLLMProvider:
    provider_name = "litellm"

    def __init__(self, default_model: str | None = None) -> None:
        self.default_model = default_model

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> LLMResult:
        try:
            litellm = importlib.import_module("litellm")
        except ModuleNotFoundError as exc:
            msg = (
                "LiteLLM adapter requires installing the optional 'llm' extra: "
                "uv sync --extra llm"
            )
            raise RuntimeError(msg) from exc
        selected_model = model or self.default_model
        if not selected_model:
            msg = "LiteLLMProvider requires a model, e.g. openai/gpt-4o-mini"
            raise ValueError(msg)
        response: Any = litellm.completion(
            model=selected_model,
            messages=[m.model_dump() for m in messages],
            tools=tools,
        )
        choice = response.choices[0]
        content = getattr(choice.message, "content", None) or ""
        usage_obj: Any = getattr(response, "usage", None)
        usage = usage_obj.model_dump() if hasattr(usage_obj, "model_dump") else {}
        return LLMResult(content=str(content), model=selected_model, usage=usage, raw={})


def create_provider(model: str | None = None) -> LiteLLMProvider:
    return LiteLLMProvider(default_model=model)
