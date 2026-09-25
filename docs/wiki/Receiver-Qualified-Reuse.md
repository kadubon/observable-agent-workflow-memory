# Receiver-qualified reuse in OAWM

Observable Agent Workflow Memory (OAWM) 0.2.0b0 adds an opt-in receiver profile.
A base certified lane is necessary but does not itself qualify a receiver.

## Qualified retrieval vs execution

```text
host Context + exact sources/inputs/dependencies
  -> independent native reconstruction -> explicit local admission
  -> current qualified retrieval -> context exposure
  -> separate action gate + use -> independent output check -> lifecycle feedback
```

The host registers contexts: receiver, workspace, mission/family, finite exact inputs,
clock, tools/protocol/evaluator, dependencies, checks and effect/exposure policy.
Memory cannot install plugins or declare its own host authority. Retrieval reloads
current memory, promotion receipt, workflow, manifest and original event bytes;
it evaluates admitted bounded candidates before ranking. Missing premises block
eligibility; malformed records raise errors.

`AgentKernel.run` uses legacy certified-memory context; its USE telemetry is not
independently verified execution. `AgentKernel.run_qualified` connects receiver
retrieval to model context and records exposure only. `ReceiverRuntime.use` is a
separate strict local boundary requiring current qualification, exact input/action,
action-bound passing receipts, explicit use cost and expected journal revision.
A retrieved view is a snapshot, not permission to act indefinitely.

## Finite execution contract

The registered `normalize-lines-v1` primitive accepts bounded text (at most 4,096
characters), takes its lines, removes duplicate lines, sorts them and joins them
with LF. It does not trim arbitrary text into a new semantic procedure or execute
prose, URLs, shell strings or serialized programs. Its implementation bytes have a
digest. A separately implemented output invariant checker checks the exact input
and output, rather than trusting the producer's success flag.

See [normalize and checked source](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/native.py),
[wire types](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/wire.py), and
[use boundary](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/runtime.py).
This finite primitive is not an arbitrary multi-step skill language.

## What changes eligibility?

Qualification is bound to receiver/context, exact input, current memory revision,
dependencies, costs and evidence. Host time must be inside `[start, expiry)`.
Changed dependencies, retirement, supersession, missing evidence or expired
qualification block later use. A scoped checked negative needs fresh later
qualification with new authoritative observation identities. Dependency withdrawal
blocks all affected receivers without deleting historical service or costs.

The use path durably reserves intent/cost before a fenced local effect. Identical
retries cannot create another service or charge. Unknown outcomes retain unresolved
state; renamed retries cannot dispatch the same pending qualification/input.
Host review is required; arbitrary outcome correction is unsupported.

## Scope and host responsibility

The store is bounded to 256 journal entries and eight registered receivers; source,
input, dependency and JSON resource limits are explicit in the
[receiver contract](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/receiver-qualified-memory.md). This is local policy,
not remote authentication, distributed ordering, tenant isolation or independent
third-party adoption. A SQLite fence is not exactly-once external execution.
Qualification never replaces permission, sandboxing or appropriate domain checks.

Authority: [lifecycle rules](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/memory-use-and-lifecycle.md) and
[independent view checker](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/checker.py).
Next: [Troubleshooting](Troubleshooting.md).
