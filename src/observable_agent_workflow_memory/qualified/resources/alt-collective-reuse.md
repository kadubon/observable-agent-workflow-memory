# Experimental receiver-qualified collective reuse

Theory: https://doi.org/10.5281/zenodo.20476200

The opt-in v0.5.0 profile forms finite inert templates, qualifies named receivers,
selects costed nonadaptive batches, and replays local source histories. It remains
Alpha research software. No external empirical collective-intelligence acceleration
experiment was performed. Synthetic results establish neither causal abstraction
value nor authenticated observations, universal transfer, indefinite growth,
AGI/ASI, settlement or execution authority.

## Installed quickstart

Download the wheel and SHA256SUMS from the GitHub Release and verify its hash.
Install the downloaded file in an isolated environment:

```text
python -m pip install ./alt_foundry_kernel-0.5.0-py3-none-any.whl
altk reuse example
altk reuse example --history --out history.json
altk reuse replay history.json 20
```

This does not use PyPI to obtain ALT. PyPI publication is not requested. Dependency
installation may use the public package index; all runtime operations are local.
The optional native interoperability checks require separately installed CCR
1.8.0, VEK 1.3.0 and CAIT 0.2.0; these are development dependencies, not mandatory
ALT runtime dependencies. `python -m alt_foundry_kernel.reuse.installed_check`
exercises packaged legacy fixtures, CLI commands and the native integration with
socket connections disabled.

## Formation and qualification

`Formation`, `Trace`, `Candidate`, `Check` and `Offer` are closed documents in
`schemas/reuse/`. `form(request)` accepts either one exact checked artifact or a
whole recurring typed sequence from at least two declared training episodes.
The deliberately small grammar has named immutable primitives, integer/string
literals and references to earlier typed outputs. Explicitly registered literal
positions may become named parameters. Repeated parameter names preserve equality.
No text similarity, code generation, arbitrary synthesis or token execution occurs.

At most eight traces, eight steps per trace, eight arguments per step, 16 named
interfaces and 16 parameter positions are supported. Extraction visits are bounded
by the registered limit (maximum 1,024). Exhaustion or failure leaves an attempted
formation charge payable; the caller must ingest its explicit failure/cost records.
Read-only formation never initializes a journal or silently writes that charge.

Original UTF-8 source strings and their hashes are retained. Candidate reconstruction
checks every projected slot against those bytes without calling the extractor.
Failures, unresolved work, taint and guards remain attached. Failed or incomplete
sources cannot qualify. The supported dependency closure consists of the registered
immutable primitive implementations; arbitrary unresolved dependencies fail closed.
Held-out or post-registration-cutoff traces cannot be mined.

An offer binds the candidate, receiver, mission, context, exact finite input domain,
task family, quality/estimand/valuation, protocol/evaluator, conditions, restrictions,
cost identities and validity interval. Its raw check sources must match these
bindings. Changing A to B or C does not transfer the evidence. Qualification is
structural source replay; source authentication and scientific validity remain
unestablished. Check declarations are not replaced with legacy `status=valid` flags.

The optional finite adapter supports only explicit field selection, renaming and
positive exact unit scaling. It returns dropped fields and does not assert semantic
equivalence. Input domains, clocks and units must belong to the declared mission
contract; there is no cross-clock or cross-mission inference.

## Registered selection

`Contract` registers at most 12 options, eight receivers, 24 opportunities, eight
joint scenarios, eight resource coordinates and 16 integer slots. Exact subset
enumeration visits at most 4,096 subsets (or a smaller requested expansion limit).
No hidden scenario is available to the selector. Scenario-dependent activation uses
only registered prerequisite success; all batch occupancy remains reserved.

Options include preparation, transfer, refresh, existing reuse, new reuse and
from-scratch service. Feasibility enforces prerequisites/timing, conflicts, hazards,
receiver qualification, service floors, deadlines, typed budgets and joint slot
occupancy. Required work can remain necessary even when no abstraction has positive
surplus. Optional all-negative investment permits no-op. Unresolved work is never
interpreted as completed service or released capacity.

After feasibility, maximize the minimum joint-scenario net value, then minimize
incremental valued cost. This is conditional on an explicit, complete valuation
and a registered separable opportunity model. Unknown joint effects must be encoded
as conflicts or explicit AND bundles, or rejected. Unique opportunity IDs cannot
receive duplicate OR credit. AND bundles are jointly checked; no synergy or
submodularity is inferred.

Every physical cost has one identity, a stage, a unit and receiver allocations
summing exactly to its amount. Shared setup is charged once. All required source
and formation charges must be present. Full-lifecycle cost includes sunk charges;
the objective uses incremental cost symmetrically for every comparison catalogue.
A changed scope/study cannot reset the journal or erase its charges.

For the deterministic control, setup costs 12, each reuse costs 1, and each matched
from-scratch service costs 5. Three uses break even at 15; four reuse services cost
16 versus 20, a modeled saving of 4. Transfer cost 5 changes selection back to
from-scratch. This is an exact finite model result, not an observed effect size.

`compare` reoptimizes all, scratch, already-available and no-transfer catalogues.
`comparison_report` reports joint-scenario surplus only when both searches finish
and have feasible checked incumbents. Incomplete search has no superiority claim.
Checker prerequisite visits have a registered ceiling of 100,000; exhaustion fails
closed. The independent checker reconstructs constraints, costs and scenarios without
importing the selector. It checks feasibility and score, not a submitted claim of
global optimality. A separate tiny oracle tests the finite selection result.

## Local lifecycle

`Journal` contains bounded source envelopes for formation, qualification, transfer,
request/result, costs, expiry, contradiction, withdrawal, refresh and correction.
Replay is pure and bounded to 256 events. Event and recorded times preserve frozen
cutoffs. Successful service identity includes artifact, receiver/context, task/input
and protocol/evaluator. Retry delivery is idempotent; conflicting IDs fail. Copies
do not create stock. A failed use invalidates that exact receiver/input scope.
Refresh requires reconstructed evidence after the invalidation; it cannot refresh
every receiver. Dependency withdrawal propagates future ineligibility while keeping
past uses and costs. Artifact identity commits primitive implementation bytes/types, dataflow and
parameters under first-occurrence alpha-renaming. Attempt or parameter renaming
does not create stock or clear revocation. Broader semantic equivalence is unsupported.

`at_history` checks the expected revision, scope/study and carried-forward costs,
then disables options whose current qualification is absent or revoked. Already
completed opportunities satisfy the existing service floor but contribute no future
value and cannot be selected for duplicate credit. Any pending
local obligation conservatively blocks the supported batch until reconciliation.
It never treats historical cumulative capital as currently eligible stock. The
legacy kernel remains unchanged: repeated legacy admissions can increment its
historical capital field, and suspension/deprecation retain that historical value.
`inspect_kernel` explicitly refuses to promote those declarations into new-profile
receiver evidence. No new-profile operation invokes a settlement transition.

Corrections append a linked cost interpretation; original source bytes and as-of
reports remain intact. Quantity corrections for other event families are currently
unsupported. `ingest` alone writes local state, with an expected digest and atomic
temporary-file replacement. The host must serialize writers across read/check/write.
There is no distributed transaction, cross-process reservation or external exactly-once
execution guarantee. CCR retains concurrent admission and execution authority.

## Input and API boundaries

Parsing rejects duplicate keys, floats/nonfinite quantities, Boolean quantities,
unknown fields/versions, oversized sources and dependency cycles. New arithmetic
uses canonical rational strings with 128-bit input coordinates. JSON is limited to
2 MB, 50,000 nodes and depth 24. Schemas resolve locally; sources contain inert data.
Legacy schemas, floating interfaces, commands and conformance goldens are preserved.

CLI operations are `example`, `form`, `qualify`, `inspect`, `plan`, `check-plan`,
`compare`, `ingest`, `replay`, and `export`. All except explicit ingestion and named
output files are read-only. Use `altk reuse COMMAND --help` for arguments.

Python entry points live under `alt_foundry_kernel.reuse`: `formation.form` and
`reconstruct`, `qualification.qualify` and `adapt`, `planning.select` and
`comparison_report`, `checker.check_plan`, `lifecycle.replay` and `ingest`, and
`bridge.at_history`. Packaged examples create synthetic input objects, not receipts.
