# Observable Agent Workflow Memory

OAWM is a local-first workflow-memory verification kernel: observable traces become
evidence-bound procedural memories whose reuse depends on declared conditions.
It addresses procedural memory for AI agents, not arbitrary factual truth.

> Can this particular workflow memory still be reused by this receiver, for this
> input, with these dependencies and this evidence?

Source and GitHub prerelease **0.2.0b0 are Beta**. The base profile retains schema
1.1; receiver-qualified reuse is opt-in and has separate versioned records.
The release was published September 21, 2026. These guides were source-checked
September 25, 2026; they do not requalify the release.

OAWM is not a general agent framework, vector-memory database, universal semantic
verifier or sandbox. It does not turn natural-language traces into arbitrary
executable programs. Retrieval is not permission to execute, and release checks
are not empirical evidence of improvement for arbitrary agents.

## Choose a reading path

- **Understand:** [When to use OAWM](When-to-Use-OAWM.md) ->
  [Concepts and lifecycle](Concepts-and-Lifecycle.md) -> [Evidence and limitations](Evidence-and-Limitations.md).
- **Integrate:** [Getting started](Getting-Started.md) ->
  [Receiver-qualified reuse](Receiver-Qualified-Reuse.md) -> [Integration guide](Integrating-with-Existing-Agents.md).
- **Inspect contracts:** [core models](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/core/models.py),
  [schemas](https://github.com/kadubon/observable-agent-workflow-memory/tree/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/schemas/), [receiver wire types](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/qualified/wire.py),
  [native contracts](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/alt-interoperability.md), and [Troubleshooting](Troubleshooting.md).

## Authoritative sources and research

The [README](https://github.com/kadubon/observable-agent-workflow-memory#readme)
provides the primary entry point. These pages explain and navigate;
[receiver rules](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/receiver-qualified-memory.md), [lifecycle rules](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/memory-use-and-lifecycle.md),
[security model](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/security_model.md) and source contracts remain authoritative.
The [publication record](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/publication-0.2.0b0.md) is historical evidence.

Research background: [English Collective Intelligence Index](https://kadubon.github.io/github.io/collective-intelligence-index.html)
and [Japanese index](https://kadubon.github.io/github.io/collective-intelligence-index.ja.html).
Research relationships are not automatic integration or deployment claims.

Next: [When to use OAWM](When-to-Use-OAWM.md).
