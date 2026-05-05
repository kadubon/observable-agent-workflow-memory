# Plugin Guide

Third-party extensions should implement one of the public ports:

- `LLMProvider`
- `StorageBackend`
- `Retriever`
- `Checker`
- `WorkflowProposer`
- `ToolAdapter`

Expose the implementation through the matching entry-point group:

- `oawm.llm_providers`
- `oawm.storage_backends`
- `oawm.retrievers`
- `oawm.checkers`
- `oawm.proposers`
- `oawm.tool_adapters`
- `oawm.receipt_verifiers`

Adapters must not depend on each other directly. Runtime code wires ports
together.

`AgentKernel.open(..., plugins={...})` accepts injected objects for:

- `storage`
- `retriever`
- `llm_provider`
- `checkers`
- `proposer`
- `tool_adapter`

This is the preferred path for applications that embed OAWM without using entry
points.

String plugin names are also accepted:

```python
kernel = AgentKernel.open(
    ".oawm",
    plugins={"llm_provider": "mock", "proposer": "deterministic"},
)
```

Custom storage backends must either implement `search_memory(...)` or be paired
with an explicit retriever plugin. The runtime fails closed if neither is true.

Use `observable_agent_workflow_memory.testing` contract helpers to validate
third-party providers, checkers, and storage backends without copying internal
tests.

Minimal package layout:

```text
my-oawm-plugin/
  pyproject.toml
  src/my_oawm_plugin/
    __init__.py
    provider.py
```

Example entry point:

```toml
[project.entry-points."oawm.llm_providers"]
my_provider = "my_oawm_plugin.provider:create_provider"
```

Contract helper usage:

```python
from observable_agent_workflow_memory.testing import assert_llm_provider_contract
from my_oawm_plugin.provider import create_provider

def test_provider_contract():
    assert_llm_provider_contract(create_provider())
```

See `examples/custom_proposer_plugin` for a proposer plugin skeleton and
`examples/action_bound_tool` for an action-bound tool flow.

LiteLLM is an optional adapter dependency. Core, storage, retrieval, checker, and
mock-provider workflows do not require installing model SDKs.
