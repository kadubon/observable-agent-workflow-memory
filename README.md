# Observable Agent Workflow Memory

`observable-agent-workflow-memory` v0.2.0b0 beta is a local-first Python package and CLI for
long-running agents that need memory they can rely on without a hidden
meta-controller. It turns short-term observable traces into verified workflow
memory.

OAWM certifies evidence-bound procedural admissibility for memory reuse. It does
not certify factual truth, model truthfulness, or real-world safety. A certified
memory is allowed for reuse under declared evidence and checks; it is not
globally true by definition.

This project is a workflow-memory verification kernel. It is not a general agent
framework and not a general-purpose memory database.

```text
observable events -> raw memory -> candidate -> verified shadow -> certified workflow
```

The repository exists to answer a narrow operational question:

> Which memories may a long-running agent safely reuse as workflow capability?

OAWM does not treat summaries, vector hits, or raw LLM outputs as durable
capability. A memory becomes admissible only after it is bound to observable
events, event digests, an evidence manifest, checker results, a promotion
receipt, and an explicit promotion step.

## What You Can Do

- Append observable events from code or JSONL.
- Build raw short-term memory automatically from those observations.
- Propose candidate workflow memories from one run.
- Verify candidates with deterministic, fail-closed checkers.
- Promote passing candidates into reusable `WorkflowContract` records.
- Retrieve only admissible certified memories by default.
- Keep failed, contradicted, superseded, and tombstoned memories audit-visible.
- Run with the mock provider immediately, or connect any LLM through an adapter.
- Replace storage, retrieval, checkers, proposers, tools, and model providers.

## Why It Is Different

- **No-meta / observable-only:** ordering is based on stored `obs_seq` and
  `obs_time`, not on an unverifiable hidden evaluator.
- **Version-bound memory:** every `MemoryRecord` has `memory_id`, `update_id`,
  and `content_digest` references in read/use/verify/correct/promote telemetry.
- **Workflow memory, not note memory:** long-term capability is represented as a
  checked workflow contract, not a summary cache.
- **Append-only receipts:** verification receipts and evidence manifests are
  inserted as new records. A newer passing receipt cannot overwrite an older one.
- **Action-bound external effects:** strict mode requires an `ActionIntent` and
  a passing receipt bound to that exact action before external-effect tools run.
- **Model independent:** `core` does not import LiteLLM, OpenAI SDKs, vector
  databases, FastAPI, cloud SDKs, or hosted services.
- **Forkable architecture:** ports and adapters keep third-party integrations
  small and testable.

## Ten-Minute Tutorial

Install and run the deterministic path first:

```powershell
uv sync --extra dev
uv run oawm init .oawm
```

Observe events:

```powershell
uv run oawm observe examples/minimal_litellm_agent/sample_events.jsonl --run-id demo
```

Propose, verify, promote, and search:

```powershell
uv run oawm propose --run-id demo --max-steps 4
uv run oawm verify <candidate-id>
uv run oawm promote <candidate-id>
uv run oawm search "workflow" --mode admissible
```

Run with mock LLM memory context:

```powershell
uv run oawm run "Use the certified workflow memory."
```

Connect a real model through LiteLLM:

```powershell
uv sync --extra llm
$env:OPENAI_API_KEY="..."
uv run oawm run --model openai/gpt-4o-mini "Summarize the certified workflow state."
```

Retire or record contradiction without erasing audit history:

```powershell
uv run oawm retire <memory-id> --reason "obsolete contract"
uv run oawm contradict <memory-id> "new observable claim" --reason "conflicting evidence"
```

Try the action-bound tool path without API keys:

```powershell
uv run python examples/action_bound_tool/run_demo.py
```

## Python API

```python
from observable_agent_workflow_memory.runtime.kernel import AgentKernel

kernel = AgentKernel.open(".oawm")

kernel.observe("note", {"text": "verify receipts before reuse"}, run_id="demo")
candidate = kernel.propose_memory("demo")
receipt = kernel.verify(candidate.memory_id)

if receipt.result == "passed":
    certified = kernel.promote(candidate.memory_id)

memories = kernel.retrieve("verify workflow", mode="admissible")
```

Action-bound tools:

```python
from observable_agent_workflow_memory.core.models import ActionIntent
from observable_agent_workflow_memory.ports.tools import ToolCall

candidate = kernel.propose_memory(
    "demo",
    tools=["write_file"],
    resource_caps={"max_steps": 4},
)
intent = ActionIntent.create(
    tool_name="write_file",
    effect_class="local-external",
    arguments={"path": "out.txt", "text": "hello"},
    resource_caps={"max_steps": 4},
)
receipt = kernel.verify(candidate.memory_id, action_intent=intent)
gated = ActionIntent.create(
    tool_name="write_file",
    effect_class="local-external",
    arguments={"path": "out.txt", "text": "hello"},
    required_receipt_id=receipt.receipt_id,
    resource_caps={"max_steps": 4},
)
kernel.invoke_tool(
    ToolCall(name="write_file", arguments={"path": "out.txt", "text": "hello"}, external_effect=True),
    gated,
    [receipt.receipt_id],
)
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| `Event` | Append-only observable telemetry with payload digest. Stored events add `obs_seq`, `obs_time`, and collector sequence. |
| `MemoryRecord` | A memory lane item with `memory_id`, `update_id`, claim, source events, and metadata. |
| `EvidenceManifest` | InputSet and digest manifest bound to the candidate update. |
| `PromotionReceipt` | Invocation-bound checker result with deterministic `receipt_digest`. |
| `WorkflowContract` | Promoted reusable workflow with preconditions, steps, postconditions, tools, caps, and replay spec. |
| `ActionIntent` | Digest-bound declaration of a tool/action and resource caps for external effects. |
| `ActionGate` | Fail-closed gate requiring action-bound passing receipts in strict mode. |

Memory lanes:

- `raw`: short-term observable memory, never admissible by default.
- `candidate`: proposed workflow memory.
- `shadow`: verified but not promoted.
- `certified`: admissible long-term workflow memory.
- `superseded`: replaced by a newer certified memory, retained for audit.
- `quarantine`: failed verification.
- `contradiction`: conflicting memory preserved as its own lane.
- `tombstone`: retired memory retained for audit.

## Architecture

OAWM uses ports and adapters:

```text
core <- ports <- adapters / runtime / cli
```

- `core`: domain models, canonical JSON, digests, lane transitions.
- `ports`: `LLMProvider`, `StorageBackend`, `Retriever`, `Checker`,
  `WorkflowProposer`, `ToolAdapter`, and receipt verification protocols.
- `adapters`: SQLite, FTS5, LiteLLM, mock LLM, deterministic proposer, local
  tools, and default checkers.
- `runtime`: observe, propose, verify, promote, retrieve, run, retire,
  contradict, supersede, action gate, and self-improvement orchestration.
- `cli`: thin Typer wrappers.
- `testing`: public contract helpers for downstream plugins.

Default storage is SQLite + FTS5. It is replaceable.

## Plugin Template

Entry point groups:

- `oawm.llm_providers`
- `oawm.storage_backends`
- `oawm.retrievers`
- `oawm.checkers`
- `oawm.proposers`
- `oawm.tool_adapters`
- `oawm.receipt_verifiers`

Minimal provider package:

```toml
[project.entry-points."oawm.llm_providers"]
my_provider = "my_package.provider:create_provider"
```

```python
from observable_agent_workflow_memory.ports.llm import LLMMessage, LLMResult

class MyProvider:
    provider_name = "my-provider"

    def complete(self, messages: list[LLMMessage], *, tools=None, model=None) -> LLMResult:
        return LLMResult(content="...", model=model or "my/model", usage={})

def create_provider() -> MyProvider:
    return MyProvider()
```

Use it without changing runtime code:

```python
kernel = AgentKernel.open(".oawm", plugins={"llm_provider": "my_provider"})
```

Custom storage must either implement `search_memory(...)` or be paired with a
retriever plugin. Otherwise `AgentKernel.open(...)` fails closed with a clear
configuration error.

## Security Assumptions

- v0.1.0 beta is local-first, single-user, single-agent.
- SQLite files are trusted local state; filesystem permissions are outside OAWM.
- Strict profile is the default. External effects require action-bound receipts.
- `warn` profile is experimental and is not a security mode in this beta.
- Raw, candidate, and shadow memory may be poisoned and must not be treated as
  safe context by default.
- Semantic validity depends on domain-specific checker plugins.
- Checkers validate evidence structure and deterministic bindings; they do not
  prove global truth.
- Model output can propose candidates, but cannot certify them by itself.
- Public JSON Schemas are versioned at `1.1`; storage migrations are documented
  in `migrations/`.

## Limitations

OAWM v0.1.0 beta is intentionally conservative:

- it is not a proof of truth; it verifies stored evidence bindings and workflow
  contracts, not global factual correctness;
- it is not a sandbox; external tools still need OS, network, and secret
  isolation;
- it cannot guarantee that a model will follow retrieved certified memory;
- the deterministic proposer is a baseline, not a domain expert;
- it is local-first and single-user; there is no multi-agent consensus, cloud
  sync, tenant isolation, web UI, MCP server, or distributed collector ordering;
- receipts are deterministic evidence checks, not ZK or cryptographic proof
  systems;
- APIs and schemas may change before a stable non-beta release.

## Commercial-Use Caveats

The code is Apache-2.0 licensed and designed for commercial extension, but
operators should add environment-specific controls before production deployment:

- access control and secrets management;
- backup and retention policy for append-only state;
- stronger checker sets for regulated tools;
- integration tests for custom adapters;
- monitoring around external-effect tool execution;
- a migration review process for schema changes.

## Development Checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

See `docs/theory_mapping.md`, `docs/theory_sources.md`,
`docs/security_model.md`, `docs/semantic_checkers.md`,
`docs/plugin_guide.md`, and `docs/release_checklist.md` for design details.

## Receiver-qualified reuse (opt-in)

Version 0.2.0b0 adds a finite source-bound ALT 0.5.0 round trip, named-receiver
retrieval connected to `AgentKernel.run_qualified`, gated local execution,
independently checked outcomes, scoped lifecycle feedback and CCR 1.8.0 task
proposals. Existing schema 1.1 and legacy APIs remain available. Context exposure
is not procedure execution, and qualification is not authority.

Run `oawm qualified --help` and see [the installed quickstart](docs/receiver-qualified-memory.md),
[native contracts](docs/alt-interoperability.md), [lifecycle rules](docs/memory-use-and-lifecycle.md)
and [publication evidence](docs/publication-0.2.0b0.md). Base OAWM requires no companion
or LLM SDK; native examples require explicit installation of pinned GitHub wheels.
GitHub prerelease assets are the requested channel; PyPI publication is not claimed.

Background: [collective-intelligence research index](https://kadubon.github.io/github.io/collective-intelligence-index.ja.html).
No external empirical acceleration experiment was performed.
