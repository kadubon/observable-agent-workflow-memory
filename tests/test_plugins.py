from __future__ import annotations

import pytest

from observable_agent_workflow_memory.adapters.jsonschema_checker import create_default_checkers
from observable_agent_workflow_memory.adapters.mock_llm import MockLLMProvider
from observable_agent_workflow_memory.adapters.sqlite_storage import SQLiteStorage
from observable_agent_workflow_memory.core.errors import FailClosedError
from observable_agent_workflow_memory.ports.llm import LLMMessage
from observable_agent_workflow_memory.ports.plugins import PLUGIN_GROUPS
from observable_agent_workflow_memory.runtime.kernel import AgentKernel
from observable_agent_workflow_memory.testing import (
    assert_checker_contract,
    assert_llm_provider_contract,
    assert_storage_backend_contract,
)


def test_default_checkers_are_loadable() -> None:
    names = [checker.checker_name for checker in create_default_checkers()]

    assert {
        "candidate-schema",
        "input-set",
        "evidence-manifest",
        "digest",
        "declared-tools",
        "deterministic-boundary",
        "resource-caps",
    }.issubset(names)


def test_mock_llm_satisfies_provider_shape() -> None:
    provider = MockLLMProvider()
    result = provider.complete([LLMMessage(role="user", content="hello")])

    assert result.content.startswith("mock:")


def test_plugin_groups_are_public() -> None:
    assert "oawm.llm_providers" in PLUGIN_GROUPS
    assert "oawm.checkers" in PLUGIN_GROUPS
    assert "oawm.proposers" in PLUGIN_GROUPS
    assert "oawm.receipt_verifiers" in PLUGIN_GROUPS


def test_public_contract_helpers_cover_default_plugins(tmp_path) -> None:  # type: ignore[no-untyped-def]
    assert_llm_provider_contract(MockLLMProvider())
    assert_checker_contract(create_default_checkers()[0])
    assert_storage_backend_contract(SQLiteStorage(tmp_path / "contract.sqlite"))


def test_kernel_accepts_injected_provider(tmp_path) -> None:  # type: ignore[no-untyped-def]
    provider = MockLLMProvider(response_prefix="injected")
    kernel = AgentKernel.open(tmp_path, plugins={"llm_provider": provider})
    result = kernel.run("check provider injection")

    assert result.content.startswith("injected:")


def test_kernel_accepts_entry_point_plugin_names(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kernel = AgentKernel.open(
        tmp_path,
        plugins={"llm_provider": "mock", "proposer": "deterministic"},
    )
    kernel.observe("note", {"text": "entry point proposer"}, run_id="demo")
    candidate = kernel.propose_memory("demo")

    assert candidate.memory_id.startswith("mem_")
    assert kernel.run("entry point model").content.startswith("mock:")


def test_custom_storage_without_retriever_fails_clearly(tmp_path) -> None:  # type: ignore[no-untyped-def]
    class NoSearchStorage:
        backend_name = "no-search"

        def initialize(self) -> None:
            return None

    with pytest.raises(FailClosedError, match="configure a retriever"):
        AgentKernel.open(tmp_path, plugins={"storage": NoSearchStorage()})
