# Observable Agent Workflow Memory

OAWM is a local-first workflow-memory verification kernel that turns observable
traces into evidence-bound procedural memories and controls whether those memories
are admissible for reuse under declared conditions. It provides procedural memory
for AI agents, not certification of arbitrary factual truth.

> Can this particular workflow memory still be reused by this receiver, for this
> input, with these dependencies and this evidence?

## Status and scope

Current source and published GitHub prerelease: **0.2.0b0, Beta**, Python 3.11+,
Apache-2.0. The [release](https://github.com/kadubon/observable-agent-workflow-memory/releases/tag/v0.2.0b0)
was published on September 21, 2026; this documentation was source-checked on
September 25, 2026. Legacy JSON schemas remain **1.1**; opt-in receiver records
have separate version identifiers. These are not interchangeable version numbers.

OAWM is not a general-purpose memory database, an agent framework, a universal
semantic verifier, or a sandbox. It does not maximize memory volume or discover
and execute arbitrary programs from natural-language traces. Retrievable memory
is not execution authorization. Release checks do not establish improvement of
arbitrary agents; no external empirical acceleration experiment is reported.

## What You Can Do

Use OAWM when a reusable procedure needs observable evidence, explicit promotion,
and a lifecycle that can reject stale workflow memory. A script is often enough
for a fixed operation; an ordinary store or RAG system may be enough for reference
material. See [when to use OAWM](docs/when-to-use-oawm.md).

- Observe events, propose workflow candidates, check evidence and explicitly promote.
- Retain failed, contradicted, superseded and retired memories for audit.
- Opt into exact receiver/input/dependency qualification and checked finite use.
- Embed public ports for storage, retrieval, providers, checkers and tools.

## Why It Is Different

Observable event order, version-bound evidence manifests and append-only receipts
make the reuse decision inspectable. Model output may propose a candidate; writing
“passed” cannot certify it. Domain-specific semantic assurance needs an appropriate
checker. Generic digests establish bindings, not truth or source authentication.

## Two profiles

**Base profile:** observable events -> raw memory -> candidate -> verified shadow
-> explicit promotion -> certified workflow. Verification and promotion are
separate host/runtime-controlled operations; a human click is not universally
required. Default admissible retrieval selects the certified lane.

### Receiver-qualified reuse (opt-in)

The receiver profile additionally binds host-declared contexts, exact inputs,
dependencies, evidence and expiry. Retrieval reloads authoritative records before
ranking. Exposure, gated execution, independent output checks and lifecycle
feedback remain separate. Its finite execution language supports the explicitly
registered `normalize-lines-v1` primitive: bounded text becomes sorted unique lines
joined by LF. This is not arbitrary multi-step skill execution.

| API | Meaning |
| --- | --- |
| `AgentKernel.run` | Legacy certified-memory context and USE telemetry; no independently checked procedure execution. |
| `AgentKernel.run_qualified` | Receiver-qualified context exposure through a supplied receiver runtime. |
| `ReceiverRuntime.use` | Separate strict local execution with exact action receipts, costs, output checking and reconciliation. |

See [receiver contracts](docs/receiver-qualified-memory.md),
[checked use and lifecycle](docs/memory-use-and-lifecycle.md), and
[qualified retrieval vs execution](docs/wiki/Receiver-Qualified-Reuse.md).

## Start here

- **Reader:** [English Wiki](https://github.com/kadubon/observable-agent-workflow-memory/wiki),
  [repository copy](docs/wiki/Home.md), and [when to use it](docs/when-to-use-oawm.md).
- **Implementer:** [getting started](docs/wiki/Getting-Started.md),
  [plugin guide](docs/plugin_guide.md), and [security model](docs/security_model.md).
- **Agent or contract reader:** [schemas](schemas/), [core models](src/observable_agent_workflow_memory/core/models.py),
  [receiver wire contracts](src/observable_agent_workflow_memory/qualified/wire.py),
  [native contracts](docs/alt-interoperability.md), and [troubleshooting](docs/wiki/Troubleshooting.md).

## Ten-Minute Tutorial

### Installation and offline orientation

The documented distribution channel is the GitHub prerelease, not an assumed PyPI
package. Download its wheel and
[SHA256SUMS](https://github.com/kadubon/observable-agent-workflow-memory/releases/download/v0.2.0b0/SHA256SUMS),
verify the wheel hash, then install into a virtual environment. Exact steps and a
separate source-checkout path are in [Getting Started](docs/wiki/Getting-Started.md).
Base installation needs no optional companion, API key, paid model, vector database
or cloud account. Dependency acquisition may need a network; the base orientation
uses the default mock provider offline after installation.

From a disposable working directory with OAWM installed:

```sh
oawm --help
oawm qualified resources
oawm init .oawm
```

The first two commands inspect help/bundled resources. `init` writes local SQLite
state. The Python example below also writes state, including retrieval telemetry.
Commands here were **source-checked, not executed for this documentation update**.
See the guide for a full candidate/verification/promotion path and optional demos.
A successful command or empty retrieval report does not establish eligible memory
or completed work.

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
- `certified`: base-profile long-term workflow memory; receiver eligibility is separate.
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

### Base-profile assumptions

- Local-first, single-user state is trusted; filesystem permissions remain external.
- Strict action-bound checking is the supported security profile. `warn` is an
  experimental compatibility option, not a security mode.
- Raw/candidate/shadow material may be poisoned. Certified does not mean true.
- Storage, configured checkers, permissions and execution boundaries remain trusted.
- OAWM is not a sandbox; hosts own OS/network/secret isolation and tool authority.

### Additional receiver-profile boundaries

Named receivers are local policy subjects, not remote authentication, independent
adoption, tenant isolation or distributed ordering. Host clocks and exact dependency
bindings matter. Expiry, retirement, supersession, checked negatives and dependency
withdrawal can block later reuse. Unresolved effects require host review; a timeout
is not a checked negative or successful service. See [lifecycle](docs/memory-use-and-lifecycle.md).

## Limitations

Generated != verified; verified != explicitly promoted; certified != receiver-qualified;
retrieved != used; context exposure != checked service; qualified != authorized.
Receipt integrity != source authentication, and deterministic replay != external truth.
Historical success does not establish current eligibility. Copied artifacts are not
new capability. Finite model results are not measured deployment gains, and passing
tests are not universal correctness. APIs may change before a stable release.

OAWM cannot guarantee that a model follows retrieved memory. The deterministic
proposer is a baseline, not a domain expert. There is no multi-agent consensus,
cloud sync, tenant isolation, web UI, MCP server or distributed collector ordering.
Receipts are deterministic evidence checks, not zero-knowledge or general
cryptographic proof systems.

## Ecosystem roles and interoperability

The [integration guide](docs/wiki/Integrating-with-Existing-Agents.md) distinguishes
verified native version pairs, extension points, partial exports and conceptual
complements. OAWM's publication evidence covers **ALT 0.5.0** finite native
qualification and **CCR 1.8.0** task-proposal parsing. A proposal is not admitted,
leased or executed CCR work. VEK/CAIT sidecars remain partial; no native acceptance
is claimed. Other projects' later releases do not expand this release's guarantees.
See the authoritative [collective handoff](docs/collective-handoff.md) contract.

## Evidence and documentation

[Publication evidence](docs/publication-0.2.0b0.md) records historical September 21,
2026 release qualification and public installed-artifact checks. This documentation
update does not rerun them or create new empirical evidence.
[Evidence and limitations](docs/wiki/Evidence-and-Limitations.md) separates mechanisms,
finite demonstrations, source inspection and unsupported claims.

- [Concepts and lifecycle](docs/wiki/Concepts-and-Lifecycle.md)
- [Semantic checker guidance](docs/semantic_checkers.md)
- [Theory mapping](docs/theory_mapping.md) and [theory sources](docs/theory_sources.md)
- [English Collective Intelligence Index](https://kadubon.github.io/github.io/collective-intelligence-index.html)
- [Japanese Collective Intelligence Index](https://kadubon.github.io/github.io/collective-intelligence-index.ja.html)
- [Wiki source and maintenance](docs/wiki-maintenance.md)

## Commercial-Use Caveats

[Apache-2.0](LICENSE) permits commercial extension under its terms; this is not a
production-readiness assurance. Hosts must address access controls, secrets,
backups, retention, adapter validation, external-effect monitoring and migrations.
See [SECURITY.md](SECURITY.md) for reporting security issues.

## Development Checks

Contributions should use a branch and PR, preserve evidence and lifecycle boundaries,
and satisfy applicable repository checks. For software development (not this
documentation-only update), existing checks include:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

See the [release checklist](docs/release_checklist.md) for release work;
documentation changes do not require or imply a new release. Wiki edits are maintained
in [docs/wiki](docs/wiki/) and published to the separate Wiki history.
