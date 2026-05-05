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

