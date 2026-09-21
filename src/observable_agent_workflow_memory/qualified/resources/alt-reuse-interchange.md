# Version-bound reuse interchange

Theory: https://doi.org/10.5281/zenodo.20476200

The raw-file manifest in `src/alt_foundry_kernel/reuse/fixtures/companions/manifest.json`
records producer versions, commits, source paths and SHA-256 hashes. Apache licenses
and CCR NOTICE are retained byte-for-byte. Companion repositories are read-only.

| Direction | Release and commit | Supported level | Boundary |
| --- | --- | --- | --- |
| ALT → CCR | 1.8.0, `1591e88e3b05f9b5fb06b2d0c749aad8bc0909be` | Native `ccr.task.v0.1` parser accepts open/unleased candidate work | Custom ALT sidecar admission is unimplemented in CCR; no lease, reward or execution |
| VEK → ALT | 1.3.0, `b07998135cb9dccde1e67db3c6ed77fdec847e09` | Actual capacity-report schema and scoped counter/clock checks | Aggregate counters are supplied, not replayed without original VEK journal |
| ALT → VEK | Same 1.3.0 | Finite synthetic native contract and schedule accepted by released checker | Separately declared one-slot check demand; no real host residual registration or observed capacity |
| ALT → CAIT | 0.2.0, `7d12bcf0bc4c6eae2acdd177175b6be414a274f6` | Supported source history accepted by released analyzer and independent checker | No monetary-to-capability conversion, causal attribution or arrival verdict |

CCR's own ALT importer still pins ALT 0.4.0. The stronger new profile is not silently
presented as that old interface. Exports carry an ALT-owned sidecar and explicit
missing admission; no legacy token is emitted where obligations would be lost.
Immutable input references never confer permission to fetch source bytes. Proposed
preparation, transfer and checking tasks contain completion criteria, original
revision, source/plan digests and physical costs; no executable command is supplied.

The VEK positive and false-guarantee fixtures are actual generated release fixtures.
The importer checks version, expected scope/revision/clock and work conservation.
It preserves the whole native report, assumptions, remaining work, budgets and
forecast. Observed and guaranteed rates remain null. The separate ALT demand example
registers one check per selected option plus calibration and counter-check, each
lasting one slot and consuming one check-work unit. These are explicit synthetic
planning quantities, not inferred rates. Shared exposure remains unknown; the label
counter-check does not claim empirical independence. A real host must supply its
own complete residual/service/unit registration before execution.

The CAIT converter retains the original journal and per-event projection map next
to a native source bundle. In the supported complete subset, costs, unique formation,
receiver checks, requests/results and withdrawal map to the published vocabulary.
Copies and qualification/request records do not create additional assets. The
example declares origin entirely unresolved; four uses remain service outcomes,
one artifact remains one stock item, and 16 resource units remain typed costs.
No reproduction matrix is synthesized from lineage. Cost valuation into asset
counts is absent.

The current native CAIT subset requires complete available costs, one registered
task/context per receiver and current creation evidence. Scoped expiry/contradiction,
refresh, corrections and unsupported parent mappings produce a partial ALT sidecar
with exact unmapped obligations; they are not forged into a complete native bundle.
The original source bytes remain available in that sidecar. Native parser acceptance
never establishes live host enforcement, authentication or causal validity.

`integration.run()` performs actual pinned native checks with the developer
integration dependency group. Installed artifact checks block socket connections.
False guarantees and incompatible clocks fail rather than being auto-repaired.
