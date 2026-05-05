"""Deterministic mock LLM provider."""

from __future__ import annotations

from typing import Any

from observable_agent_workflow_memory.ports.llm import LLMMessage, LLMResult


class MockLLMProvider:
    provider_name = "mock"

    def __init__(self, response_prefix: str = "mock") -> None:
        self.response_prefix = response_prefix

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> LLMResult:
        del tools
        content = messages[-1].content if messages else ""
        return LLMResult(
            content=f"{self.response_prefix}: {content[:500]}",
            model=model or "mock/model",
            usage={"prompt_messages": len(messages)},
        )


def create_provider() -> MockLLMProvider:
    return MockLLMProvider()

