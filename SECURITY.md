# Security Model

The default runtime is fail-closed. It rejects promotion when evidence is
missing, malformed, or not reproducible.

Threats considered in v0.1:

- memory poisoning through unverified raw events;
- prompt injection embedded in retrieved memories;
- stale or superseded memory reuse;
- hidden or undeclared tool input;
- receipt-bloat and checker resource exhaustion;
- schema drift without migration;
- accidental external effects without an action gate.

This library does not claim model truthfulness. It records observable evidence
and deterministic checker outcomes.

Certified memory means admissible under declared evidence and checks; it does
not mean factual truth. Raw, candidate, and shadow memory may contain prompt
injection and must not be treated as safe context by default.

External-effect tools still need operating-system, network, and secret isolation
in production. OAWM's ActionGate is an application-level gate, not a sandbox.
The `warn` profile is not a security mode.
