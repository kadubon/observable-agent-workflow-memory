# Theory Sources

This file records the RAG-derived paper identifiers and DOI bindings used as
design material. The project does not copy paper text into source; it maps
implementation invariants to source records.

RAG source: a local `paper_tex_rag` build generated on 2026-05-05 from the
paper TeX backup corpus and DOI metadata at
`https://kadubon.github.io/github.io/works.html`. The RAG database and source
manuscripts are design inputs and are not distributed in this repository.

| Theory source | Paper id | DOI | Adopted invariant |
| --- | --- | --- | --- |
| MemoryFlow | `memoryflow-real-time-implementation-agnostic-telemetry-for-measuring-dynamic-memory-qualit__15c8f004de_7321f73bc9` | `10.5281/zenodo.18136347` | Memory operations are append-only observable events. `memory_id`, `update_id`, and `content_digest` are carried in telemetry. `obs_seq` and `obs_time` are ordering authorities. |
| Controller Scale Is Not Enough | `controller-scale-is-not-enough-for-long-running-agi-workflow-theory-with-reusable-certifie__cf6cfdaa37_44f93c46ed` | `10.5281/zenodo.19690749` | Long-run capability grows through certified workflow libraries, not by treating raw summaries or model scale as durable competence. |
| Certified Service Is Not Enough | `certified-service-is-not-enough-for-long-running-agi-continuity-theory-of-recovery-authori__7a46407bdb_f9fe72a557` | `10.5281/zenodo.19719004` | Authority, identity, recovery, mutation, goal, and memory integrity checks are separate from task success. OAWM preserves those as explicit receipts and lane transitions. |
| OOPCA | `observable-only-proof-carrying-autonomy-oopca-audit-compression-and-hybrid-proof-replay-ga__c1d6ff5032_b19d2463e5` | `10.5281/zenodo.18453429` | Evidence manifests, deterministic replay digests, and fail-closed action gates are required before promotion or external effects. |
| POB-ML | `process-aware-observable-only-backcasting-meta-layer-pob-ml-audit-ready-deterministic-repl__b4243ebe69_7cded61a2d` | `10.5281/zenodo.18239203` | Verification binds exact InputSet ids and event payload digests. Missing or mismatched evidence fails closed. |
| Search Stability | `search-stability-under-finite-context-minimal-theory-of-adequacy-preservation-compression__5d3895ab98_790ec6d3dd` | `10.5281/zenodo.18905242` | Compression, reset, and summarization are candidates only. They become reusable memory only after adequacy-preserving verification. |
| Sovereign Epistemic Commons | `sovereign-epistemic-commons-under-no-meta-governance-observable-only-laws-for-shared-memor__072f7ce28d_80cfb6e072` | `10.5281/zenodo.18997828` | Contradictions, superseded memories, quarantines, and tombstones are retained as lanes instead of erased. |
| Recursive Self-Improvement Stability | `recursive-self-improvement-stability-under-endogenous-yardstick-drift-first-principles-int__8aea4defaa_c1e1c1afc6` | `10.5281/zenodo.19044634` | Self-improvement stops in shadow by default. Promotion requires explicit operator/runtime action after replay and checker success. |
| Proof-Carrying Skills | `stop-recomputing-for-ai-llms-proof-carrying-skills-for-compute-saving-inference-reuse-laye__aa653e1bfa_b503c75304` | `10.5281/zenodo.18490939` | Reusable skills are represented as contracts plus receipts, with resource caps and checker evidence. |
| Verifiable Modular Pipeline Contracts | `verifiable-modular-pipeline-contracts-for-ai-and-general-composite-systems-observable-only__5649f94cab_c0f10c5662` | `10.5281/zenodo.18529100` | Workflow contracts expose interface signatures, tools, preconditions, postconditions, resource caps, and replay specs for modular replacement. |

Implementation checkpoints:

- `src/observable_agent_workflow_memory/core/models.py`: schema 1.1 models,
  version-bound memory, receipts, manifests, action intents.
- `src/observable_agent_workflow_memory/core/transitions.py`: lane rules for
  certified, superseded, quarantine, contradiction, and tombstone.
- `src/observable_agent_workflow_memory/runtime/action_gate.py`: action-bound
  external-effect policy.
- `src/observable_agent_workflow_memory/runtime/promotion.py`: verification,
  append-only receipt creation, candidate update binding, promotion, and
  supersedence.
- `src/observable_agent_workflow_memory/runtime/self_improvement.py`: shadow
  verification without automatic promotion.
