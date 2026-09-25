# Troubleshooting OAWM reuse

Observable Agent Workflow Memory (OAWM) rejects reuse when required premises are
missing. Base schema 1.1 and receiver-profile decisions differ. Inspect the recorded
conditions before changing inputs; do not turn rejection into automatic success.

## Why is my certified memory not returned?

For base retrieval, inspect the query, lane and matching record using audit-mode
search (which records telemetry). For receiver retrieval, inspect `views`, `excluded`
and the snapshot, plus current revision, context, inputs, dependencies and expiry.
A certified lane alone does not qualify a receiver. Correct the host configuration
or obtain genuinely fresh evidence; do not substitute an audit result into an
admissible execution path.

## Why did promotion fail after verification?

Inspect the actual receipt, candidate update/content digest, manifest, required
checker set and current lane. `kernel.verify_receipt(receipt_id)` checks a real
receipt ID; `kernel.audit_receipts(strict_recheck=True)` is available for inspection.
Verification passing earlier does not bind a later edited candidate. Reverify the
intended candidate and explicitly promote only if current conditions pass. Never
forge a receipt or make an LLM-written status authoritative.

## Why does receiver A qualify but receiver B does not?

Compare the host-registered Contexts and exact receiver/input evidence in the
qualification and retrieval report. Obtain separate B evidence and host admission
where supported. Changing a receiver label on A's receipt is not qualification;
local receiver names also do not authenticate remote parties.

## Why does a previously working procedure stop qualifying?

Inspect the receiver journal and current authoritative memory for scoped negatives,
invalidation, expiry, supersession, retirement or dependency withdrawal. Refresh
requires later qualification/check times and new observation identities after a
scoped block; new implementations require new qualification. Preserve past costs
and service. Copying artifacts or renaming memory cannot clear an invalidation.

## Why is a timeout still unresolved?

Use `oawm qualified inspect` with the real initialized database path and inspect
unresolved intents and costs. An absent/unknown result is not a checked negative.
Hand off to the host for effect review; arbitrary outcome correction is unsupported.
Do not rename a retry, edit database records or reset the intent to success.

## Why is read-only inspection refusing the current store?

Check the database path, prior legacy and receiver-journal initialization, and the
reported active-WAL condition. Read-only commands never initialize state and refuse
a nonempty WAL rather than ignore newer evidence. Have the storage owner provide a
consistent transaction snapshot or perform a coordinated checkpoint. Do not delete
the WAL, copy an active database incompletely or bypass the guard.

## Why is an optional companion dependency missing?

Check which path was requested and compare installed versions with the
[pinned native requirements](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/alt-interoperability.md). Base mock usage needs
no companion; native paths need the documented wheels. Install them only when
intentionally using those paths, or remain in the base profile. Never treat a missing
checker/import as a passing check or substitute arbitrary newer versions.

## Why does successful retrieval not count as completed work?

Inspect whether the record is a view, exposure, attempted use, checked outcome or
reconciled service. `run` and `run_qualified` expose memory; they do not establish
checked procedure execution. Use the explicit supported `ReceiverRuntime.use`
boundary only when the host supplies all required evidence and authority. A zero
CLI exit means a report was produced, not that an eligible record or service exists.

## Can I bypass a failed check to make the example run?

No. Inspect the structured error, exact source/policy/version binding and relevant
contract. Repair malformed inputs, obtain missing legitimate evidence, or report an
unsupported scenario. If evidence cannot be supplied, keep the rejection. Do not
forge receipts, edit the database, disable strict gates or promote unresolved effects.

Authority: [receiver rules](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/receiver-qualified-memory.md),
[lifecycle](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/memory-use-and-lifecycle.md), [kernel inspection API](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/src/observable_agent_workflow_memory/runtime/kernel.py)
and [security model](https://github.com/kadubon/observable-agent-workflow-memory/blob/af9da7e396d8694ce3c8d1affce27cfd7a5fcfdb/docs/security_model.md).
Next: [Evidence and limitations](Evidence-and-Limitations.md).
