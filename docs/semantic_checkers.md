# Semantic Checker Plugins

Default OAWM checkers verify procedural admissibility:

- candidate schema and lane shape;
- exact InputSet ids;
- stored event payload digest consistency;
- evidence manifest schema, candidate id, update id, replay digest, and manifest id;
- candidate content digest and update id;
- declared tools;
- deterministic boundaries;
- resource caps.

They do not prove semantic correctness, factual truth, or model truthfulness.
Those properties are domain-specific and need explicit checker plugins.

## Reference Checker Templates

The module `observable_agent_workflow_memory.adapters.semantic_checkers` provides
small deterministic templates:

- `ReplaySuccessChecker`: requires explicit `replay_success == True` in evidence
  or context.
- `ToolTraceChecker`: checks declared tool names and optional argument digests
  for recorded tool invocations. It never executes tools.
- `DomainInvariantChecker`: checks that configured invariant labels have
  explicit passing records.

These are examples, not complete domain validation systems.

## Domain-Specific Checker Ideas

- `ReplaySuccessChecker`: bind a workflow to a deterministic replay run.
- `ToolTraceChecker`: verify that observed tool traces match declared tools and
  argument digests.
- `RegressionCaseChecker`: require named regression cases to pass before a
  workflow can be promoted.
- `DomainInvariantChecker`: require explicit invariant records, such as
  "schema-roundtrip", "no-network", or "resource-budget-observed".
- `HumanReviewReceiptChecker`: accept a human review record only when it is
  evidence-bound. The human is not a privileged oracle; the review must include
  reviewer id, reviewed object ids, timestamp, decision, and digest-bound scope.

## Safe Checker Guidelines

- Fail closed on missing or malformed evidence.
- Treat LLM text as evidence only when it is bound to observable ids and digests.
- Do not call tools, networks, or model APIs inside checkers.
- Keep checker inputs deterministic and serializable.
- Return structured failure reasons; do not raise for ordinary verification
  failure.
- Make domain assumptions explicit in checker names and docs.
- Do not label a passing semantic checker as truth certification.

## 0.2.0b0 receiver profile

The new normalize-lines-v1 finite checker independently tests sorted/unique output against the exact recorded input, rather than accepting replay_success flags. Its implementation/source scope and receiver evidence are documented in alt-interoperability.md. It establishes no general semantic equivalence for prose workflows.
