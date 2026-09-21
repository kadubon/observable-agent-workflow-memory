# Theory Mapping

This project translates the paper corpus into implementation invariants rather
than copying paper text into the repository.

| Theory | Implementation invariant |
| --- | --- |
| MemoryFlow | Memory is an append-only event stream. Observable order is authoritative, and every reusable memory update has a version-bound `update_id`. |
| Controller Scale Is Not Enough | Certified workflow contracts are the durable capability unit, not raw summaries. |
| Certified Service Is Not Enough | Long-running operation requires memory integrity, authority, recovery, and gate checks. |
| OOPCA / POB-ML | Promotion and external effects require evidence manifests and replay/proof receipts. |
| Search Stability | Compression and reset remain candidates until adequacy-preserving evidence exists. |
| Sovereign Epistemic Commons | Contradictions, superseded memory, quarantine, and tombstones are retained as lanes. |
| Recursive Self-Improvement Stability | Improvements run through shadow/candidate lanes before promotion. |
| Proof-Carrying Skills / VMPC | Reusable workflows carry preconditions, postconditions, caps, and receipt rules. |

The first public release implements conservative local versions of these
invariants. It does not claim to solve truthfulness or full autonomous safety.

## v0.1 Implementation Notes

- `EvidenceManifest` fixes the candidate input set before verification.
- `MemoryRecord.update_id` binds a memory content version independently from
  lane movement. Read, use, verify, correct, and promote telemetry includes
  `memory_id`, `update_id`, and `content_digest`.
- `memory_records` is only a current-value index. `memory_revisions` is the
  append-only audit trail for memory state changes.
- `EvidenceManifest` binds input event ids, event payload digests, candidate
  digest, candidate update id, replay digest, and manifest id.
- The default InputSet checker fails closed unless those ids match
  `source_event_ids` exactly and the manifest digests match the stored
  observable events.
- The default evidence-manifest checker treats externally supplied manifests as
  untrusted. It parses the manifest with the public model, recomputes
  `candidate_digest`, `replay_digest`, and `manifest_id`, and fails closed on
  mismatch.
- `retrieve` and runtime memory use emit `memory_read` / `memory_use` events
  without creating new raw memories, matching MemoryFlow telemetry separation.
- `verify` and explicit corrections emit `memory_verify` / `memory_correct`
  events, preserving MemoryFlow's operation vocabulary.
- Passing verification moves memory to `shadow`, not directly to `certified`.
- `promote` is the explicit boundary from checked candidate to admissible
  workflow memory.
- Correction promotion moves the replaced certified memory to `superseded`
  instead of deleting or rewriting it.
- `WorkflowContract.checkers` is copied from the passing promotion receipt, so
  the promoted contract records the actual verification rule set.
- `PromotionReceipt.verification_id` is invocation-bound while
  `PromotionReceipt.receipt_digest` is replay-bound; storage appends receipts
  and manifests instead of replacing them.
- `ActionGate` can open only from passing receipts bound to the exact
  `ActionIntent` used for the external effect.
- The deterministic-boundary checker rejects floats in decision-critical
  candidate metadata and evidence.

## 0.2.0b0 receiver profile

The receiver profile separates exposure, attempted execution, checked service and current eligibility. Finite ALT formation and economic comparison remain ALT-owned; lifecycle records do not become capability stock or causal evidence. See alt-interoperability.md and collective-handoff.md.
