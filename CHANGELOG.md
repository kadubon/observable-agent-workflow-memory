# Changelog

## Unreleased

- Harden documentation around evidence-bound admissibility versus factual truth.
- Expand CI to Python 3.11, 3.12, and 3.13 across Linux, Windows, and macOS.
- Add strict receipt audit that can re-run checkers against stored evidence.
- Add deterministic semantic checker templates for replay, tool traces, and
  domain invariants.
- Add local examples for certified workflow memory, ActionGate external effects,
  and semantic checker plugins.
- Clarify security limitations: strict-only public security model, no sandbox,
  SQLite as trusted local state, and `warn` as non-security compatibility mode.
