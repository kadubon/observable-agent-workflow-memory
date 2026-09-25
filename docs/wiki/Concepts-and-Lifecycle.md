# OAWM concepts and lifecycle

Observable Agent Workflow Memory (OAWM) preserves an inspectable agent memory
lifecycle. This page describes base schema 1.1 and distinguishes the additional
receiver-profile journal shipped in 0.2.0b0.

```text
observable events -> raw -> candidate -> verified shadow
                                  |            |
                           failed checks   explicit promotion
                                  |            |
                             quarantine    certified
                                               |
                              superseded / contradiction / tombstone
```

The diagram is an orientation, not the complete transition table.
[Lane rules](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/core/transitions.py) are authoritative.
Raw memory captures observations; candidate is proposed workflow memory; shadow
has passed verification but is not promoted. Certified is the base reuse lane.
Superseded means replaced; quarantine preserves failed checks; contradiction
preserves conflicting material; tombstone retains retired memory for audit.
These lanes are not a truth ranking and tombstones are not a deletion mechanism.

## Records and version identity

| Record | Purpose |
| --- | --- |
| `Event` | Observable telemetry with payload digest; stored order uses `obs_seq` and `obs_time`. |
| `MemoryRecord` | Lane item bound by `memory_id`, `update_id` and content digest. |
| `EvidenceManifest` | Exact candidate update, input event set and digests, plus replay binding. |
| `PromotionReceipt` | Invocation-bound checker result with deterministic receipt digest. |
| `WorkflowContract` | Promoted preconditions, steps, postconditions, tools, caps and replay specification. |
| `ActionIntent` | Exact action/tool arguments and resource-cap binding for external effects. |
| `ActionGate` | Strict fail-closed boundary requiring matching passing action receipts. |

[Core models](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/core/models.py),
[promotion](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/runtime/promotion.py) and
[action gate](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/runtime/action_gate.py) define these contracts.
A matching name is insufficient: a receipt for a different update or action cannot
stand in for the required binding. Receipts and manifests are appended, not overwritten.

## Verification is not promotion

The host/runtime explicitly invokes promotion after verification. An LLM may
propose a candidate but cannot certify it by writing a successful status field.
This explicit boundary does not impose a human click on every installation.
Default schema/digest checks do not prove domain semantics; appropriate
[semantic checkers](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/semantic_checkers.md) are allowed and necessary for such claims.

## Receiver-profile feedback

Receiver records use `oawm_receiver_v1`, `oawm_qualification_v1` and
`oawm_lifecycle_v1` identifiers, not a replacement for base schema 1.1.
Exposure is separate from attempted use, checked outcome and reconciled service.
A checked negative or explicit host invalidation blocks the relevant
artifact/context/input scope. Imported allegations do not authenticate revocation.
Refresh needs later valid evidence and new observation identities; renaming a memory
or copying an old receipt does not clear a block.

Expiry, supersession, retirement and withdrawal of an exact dependency block future
reuse while preserving past costs/outcomes. Timeout or unknown effects remain
unresolved; they cannot be reset to success. Host clocks and local storage remain
trusted. See [checked use and lifecycle](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/memory-use-and-lifecycle.md).
Next: [Receiver-qualified reuse](Receiver-Qualified-Reuse.md).
