# Integrating OAWM with existing agents

Observable Agent Workflow Memory (OAWM) owns procedural qualification and checked
reuse. Its base ports and opt-in receiver profile do not make it the complete
collective task runtime. The labels below describe OAWM's own integration scope,
not a feature ranking or certification of every other project's current release.

## Documented extension points

The [plugin guide](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/plugin_guide.md) describes `LLMProvider`, `StorageBackend`,
`Retriever`, `Checker`, `WorkflowProposer`, `ToolAdapter` and receipt-verifier entry
points. `AgentKernel.open(..., plugins={...})` accepts host configuration and injected
implementations. Custom storage needs `search_memory(...)` or an explicit retriever.
The base architecture is `core <- ports <- adapters / runtime / cli`.

These are **documented extension points**, not claims that arbitrary plugins are
tested or safe. Host configuration must not come from imported memory. The receiver
path evaluates authoritative bounded local records rather than trusting arbitrary
retriever lane labels. Fixed native imports do not imply a general adapter loader.

## Native version-bound interoperability

**ALT (Abstraction Liquidity Theory): verified native interoperability for ALT 0.5.0 in the historical OAWM
0.2.0b0 qualification.** OAWM preserves source bytes and field mappings through
finite formation, receiver qualification, reconstruction and economic comparison.
ALT owns the supported abstraction/reuse qualification and economic model.
This is not universal transfer or empirical savings.

**CCR (Collective Capability Runtime): verified native proposal parsing for CCR
1.8.0 in that qualification; partial handoff beyond parsing.** CCR owns applicable
task/runtime coordination. OAWM exports an open, unleased task-shaped proposal with
`host_admission_required` true. Parsing does not accept work, reserve capacity,
grant a lease, dispatch, settle or reward. The CCR 1.8.0 ALT token importer targets
ALT 0.4.0; OAWM's stronger sidecar is not silently enforced by it.
This is a pinned-version limitation, not a claim about every newer CCR release.

Authority: [native pins/contracts](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/alt-interoperability.md),
[collective handoff](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/collective-handoff.md) and
[historical publication evidence](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/publication-0.2.0b0.md).
Do not upgrade companions merely because newer releases exist.

## Partial sidecars and exports

**VEK (Verification Ecology Kit): partial sidecar/export.** Its relationship here is
bounded verification-work/capacity modeling; OAWM does not supply native capacity
registration/source journals.

**CAIT: partial sidecar/export.** Its relationship here is accounting for supported
evidence, costs and service/capability distinctions; OAWM lacks the native registered
source-accounting contract and origin evidence. Neither sidecar establishes native
acceptance, rate, causal contribution, settlement or monetary-to-capability conversion.
See [handoff obligations](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/collective-handoff.md).

## Conceptual complements and externally owned composition

- **MemoryFlow: conceptual complement in this OAWM release.** It audits declared
  memory behavior and telemetry, rather than admitting procedures. See its
  [project description](https://github.com/kadubon/memoryflow-agent-memory-auditor).
  Shared vocabulary is not an installed, tested OAWM adapter.
- **CMGL (Certified Memory Governance Layer): conceptual complement in this release.**
  It governs memory admission and backend/context boundaries. See its
  [project description](https://github.com/kadubon/certified-memory-governance-layer).
  Conceptual compatibility does not establish end-to-end integration.
- **OASG (Observable-only Autonomic Slack Gradient): externally owned composition,
  not an OAWM native integration claim.**
  It evaluates bounded workflow-policy changes; see
  [OASG's own contracts and evidence](https://github.com/kadubon/oasg).
  A composition using OAWM elsewhere does not transfer task-runtime ownership to OAWM.

These role descriptions are source-inspected orientation, not new compatibility tests.
Remote authenticated receivers, arbitrary skill execution, distributed stores and
automatic cross-project admission are **unsupported claims** for this OAWM release.
Next: [Evidence and limitations](Evidence-and-Limitations.md).
