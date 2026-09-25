# When to use OAWM

Observable Agent Workflow Memory (OAWM) is useful when long-running agents need
verified workflow memory with inspectable evidence and a lifecycle for rejection.
The base profile controls workflow promotion; the opt-in receiver profile adds
current receiver/input/dependency qualification and finite checked use.

## Is OAWM a replacement for RAG or a vector-memory database?

No. Retrieval-augmented generation retrieves reference material for model context.
OAWM governs whether a procedural memory is admissible under declared checks.
Its default SQLite/FTS5 storage is an implementation choice, not a vector database.
A retriever port is an extension point, not proof of integration with any vector store.
Neither similarity nor a retrieved document establishes execution authority.

## When should a trace become a reusable procedure?

When the host can define a bounded workflow contract, preserve the exact observable
inputs, provide appropriate checks, and explicitly promote a passing version.
Raw traces and summaries remain proposals. Base verification checks bindings;
domain semantics need domain checkers. Receiver use additionally requires fresh
qualification for the actual context, inputs and dependencies.

## When is a simpler script or ordinary store enough?

Use a script for a fixed operation if versioned memory admission and lifecycle
feedback add no value. Use an ordinary store for notes or facts when you need
storage/retrieval rather than evidence-bound procedural reuse. OAWM adds complexity
if you cannot provide meaningful checks, maintain evidence, or act on invalidation.
It is not a way to make arbitrary saved text trustworthy.

## What must the host provide?

Trusted local storage, filesystem permissions, clock policy, configured checkers,
and controlled tool implementations. The receiver profile also needs explicit
Context registration, exact inputs/dependencies, source observations, costs and
admission. Hosts own model selection, effect authorization, isolation and unresolved
effect review. Receivers are local policy subjects, not authenticated remote tenants.

See the authoritative [security model](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/security_model.md),
[checker guidance](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/semantic_checkers.md), and [receiver contract](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/receiver-qualified-memory.md).
Next: [Getting started](Getting-Started.md).
