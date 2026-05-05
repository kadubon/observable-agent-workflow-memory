# Security Model

The system assumes that raw memory can be poisoned. Therefore raw and candidate
memory are not admissible by default.

Prompt injection inside stored memory is expected. The default retrieval mode
returns only certified memory, and certified means admissible under evidence and
checks, not true.

The v0.1.0 beta public security model is strict-only. The `warn` profile remains
an experimental compatibility knob and must not be treated as a security mode.

Fail-closed cases:

- missing InputSet evidence;
- InputSet ids that do not exactly match candidate source events;
- InputSet digest values that do not match stored observable event payloads;
- invalid evidence manifest schema;
- evidence manifest candidate mismatch;
- evidence manifest candidate update mismatch;
- declared tool mismatch between candidate, evidence, contract, and invocation;
- replay digest mismatch;
- manifest id mismatch;
- candidate digest mismatch;
- missing input event digests;
- decision-critical float values in candidate metadata or evidence;
- malformed schema;
- checker gas/resource cap violation;
- external-effect tool call without an action-bound ActionGate receipt;
- replay receipt absence where a strict profile requires it.

Quarantine is not deletion. It is an audit lane.

Externally supplied evidence is untrusted input. The default checker set parses
the manifest, then recomputes the candidate digest, replay digest, and manifest
id from the stored candidate and authoritative InputSet digests.

Semantic validity is delegated to domain-specific checker plugins. The default
checkers verify bindings, schemas, digests, declared tools, deterministic
boundaries, and resource caps; they do not prove that a workflow claim is
factually correct.

External effects are blocked unless the caller supplies an `ActionIntent` and a
passing `PromotionReceipt` bound to that exact action id. A passing receipt for
one candidate or one action cannot open a different external effect. The local
tool adapter also requires an internal runtime token, so passing
`{"action_gate_open": true}` directly to the adapter is not sufficient.

This is not a sandbox. Tool implementations still need normal OS-level,
network-level, and secrets-management controls in production.
