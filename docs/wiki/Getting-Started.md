# Getting started with OAWM

Observable Agent Workflow Memory (OAWM) 0.2.0b0 is a Beta GitHub prerelease.
This guide separates base usage from opt-in receiver reuse. Commands and API names
were checked against source on September 25, 2026, **not executed for this guide**.
Dependency installation may use the network; subsequent mock/base usage needs no
API key, paid model, cloud account or vector database.

## Install the released wheel

Use Python 3.11+ and a virtual environment. From the actual
[release](https://github.com/kadubon/observable-agent-workflow-memory/releases/tag/v0.2.0b0),
download `observable_agent_workflow_memory-0.2.0b0-py3-none-any.whl` and
[SHA256SUMS](https://github.com/kadubon/observable-agent-workflow-memory/releases/download/v0.2.0b0/SHA256SUMS)
to the same directory. Compare the wheel's SHA-256 with its entry in SHA256SUMS
before installation. Hash equality checks bytes, not source authentication.
OAWM and ALT installation from PyPI is not assumed.

POSIX shell, from that download directory (stop if the comparison fails):

```sh
sha256sum observable_agent_workflow_memory-0.2.0b0-py3-none-any.whl
cat SHA256SUMS
python -m venv .venv
.venv/bin/python -m pip install ./observable_agent_workflow_memory-0.2.0b0-py3-none-any.whl
.venv/bin/oawm --help
.venv/bin/oawm qualified resources
```

PowerShell alternative, from that directory (stop if the comparison fails):

```powershell
Get-FileHash .\observable_agent_workflow_memory-0.2.0b0-py3-none-any.whl -Algorithm SHA256
Get-Content .\SHA256SUMS
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .\observable_agent_workflow_memory-0.2.0b0-py3-none-any.whl
.\.venv\Scripts\oawm.exe --help
.\.venv\Scripts\oawm.exe qualified resources
```

Help and resources do not initialize runtime state. No companion is needed here.
Use that environment's Python and `oawm` below (activate it, or use full executable paths).

## Base-profile orientation

From a disposable working directory, save the following as a Python file and run
it with the installed environment's Python. No checkout or sample JSONL is needed.
`AgentKernel.open` initializes `.oawm/oawm.sqlite`; observation, proposal,
verification, promotion and retrieval telemetry write local state.

```python
from observable_agent_workflow_memory.runtime.kernel import AgentKernel

kernel = AgentKernel.open(".oawm")
kernel.observe("note", {"text": "verify receipts before reuse"}, run_id="demo")
candidate = kernel.propose_memory("demo")
receipt = kernel.verify(candidate.memory_id)
if receipt.result == "passed":
    kernel.promote(candidate.memory_id)
memories = kernel.retrieve("verify workflow", mode="admissible")
```

This demonstrates API wiring, evidence binding and explicit workflow promotion,
not arbitrary semantic correctness or checked procedure execution. IDs come from
actual returned objects. Passing verification only reaches shadow; promotion is a
separate host/runtime decision. The default provider is mock; configuring a real
provider changes the operational requirements.

## Source-checkout development is a separate path

From the repository root, the existing development setup is `uv sync --extra dev`;
use `uv run oawm` for CLI commands. This installs development dependencies, unlike
the base release-wheel path. The existing sample flow is `uv run oawm init .oawm`,
then `uv run oawm observe examples/minimal_litellm_agent/sample_events.jsonl --run-id demo`
and `uv run oawm propose --run-id demo --max-steps 4`.
Use the actual returned candidate ID as the argument to `uv run oawm verify` and,
only after passing checks and an explicit promotion decision, `uv run oawm promote`.
These are state-writing operations. `uv run oawm search "workflow" --mode admissible`
also records retrieval telemetry. No fabricated output or ID is supplied here.

## Receiver-qualified orientation

`oawm qualified --help` exposes the separate CLI. Base `init` does not initialize
the receiver journal or admit qualifications. Host code calls `Store.initialize()`
after legacy initialization, registers explicit `Context` records, and uses
`ReceiverRuntime.admit` against the expected journal revision with valid evidence.
See the [source example](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/example.py)
and [lifecycle contract](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/memory-use-and-lifecycle.md) for the complete setup.

For an already initialized receiver-profile database, read-only inspection is:

```sh
oawm qualified inspect .oawm/oawm.sqlite
```

Use the real database location if different. Inspection does not create missing
state. `qualified retrieve` additionally needs the host Context JSON list, registered
receiver, exact input text and host integer time. For POSIX shells, an illustrative
argument construction is `input_text=$(printf 'b\na\nb')`; for PowerShell it is
``$inputText = "b`na`nb"``. These are actual newline characters, not literal backslash-n.
Supply the host's real policy, receiver and time; examples do not invent them.
`qualified check` reconstructs a qualification file at a supplied time;
`qualified export` emits an inert proposal. Neither admits or executes the proposal.
A successful exit means a valid report, which may contain no eligible views.

## Optional native companions and demos

Only install companions if deliberately exercising native paths. The
[pinned installation instructions](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/alt-interoperability.md) specify ALT 0.5.0
and CCR 1.8.0 wheel hashes. Newer versions are not interchangeable by assumption.
The optional `oawm qualified example` creates disposable local state and a result
file, checks outcomes, then cleans up. It is a finite synthetic demonstration,
not an empirical acceleration experiment. It was not run for this documentation task.
The base [action-bound example](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/examples/action_bound_tool/README.md) and
[plugin guide](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/plugin_guide.md) remain available for deliberate development work.

Authority: [base CLI](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/cli/app.py),
[qualified CLI](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/cli.py),
[kernel](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/runtime/kernel.py).
Next: [Concepts and lifecycle](Concepts-and-Lifecycle.md).
