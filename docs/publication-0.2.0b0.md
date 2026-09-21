# 0.2.0b0 publication record

Preflight found clean main `414299d4d15b5de434f5fb1ccbb4ba17df9155ff`, package
0.1.0b0, no tags/releases/open PRs, and no active rulesets or main branch protection.
The account could read branch policy. The Wiki flag was enabled but its git repository
did not exist: **NOT_APPLICABLE**, not created. Suggested 0.2.0b0 was unused.

Baseline: 43 tests passed on Windows/Python 3.14.6. Baseline coverage is retained
separately in qualification evidence; the new 95% statement/90% branch gates are
introduced for every new qualified-profile module, including unimported modules.
They are not represented as historical whole-project guarantees. Existing
Linux/Windows/macOS × Python 3.11/3.12/3.13 gates remain intact.

Baseline statements: 1,362/1,594 (85.45%); branches: 238/366 (65.03%). The final
source-run report records whole-suite and new-profile coverage separately.

The implementation covers receiver/source qualification, actual native ALT round
trip, runtime-qualified exposure, action-gated local use, checked outcomes and
scoped lifecycle feedback, native CCR proposals and explicit partial VEK/CAIT
sidecars. Prose workflows do not become typed programs. The new profile is opt-in.

Two focused security corrections reject empty promotion checker sets and altered
ActionIntent fields retaining an old action ID. The SQLite adapter now closes
connections after transactions. Legacy identifiers, schemas, receipt encodings and
normal API behavior are preserved. No companion or website files were modified.

Dependency audit required click >=8.3.3; the older optional LiteLLM pin prevented
resolution, so its compatible version and related click/Typer resolution were
updated together. idna and urllib3 were targeted separately. No known vulnerabilities
remained in the audited development/integration environment. OAWM and ALT have no
PyPI advisory entry, so their source/test checks remain distinct from dependency audit.

Seven selected implementation faults target omitted receiver checks, skipped
withdrawal, source-digest bypass, exposure-as-success, duplicate service, hidden
unmapped fields and waived ActionGate checks. This is a bounded selected set,
not a whole-project mutation guarantee.

The distribution workflow builds wheel/sdist once per commit and checks those
same wheel bytes on Linux/Windows/macOS under Python 3.11 and 3.13. A separate
Linux/Python 3.13 job installs the sdist. Each artifact gets fresh, cache-disabled
base and native-companion environments outside the checkout. Tests cover package
metadata/import origin, literal pip check, CLI help, resources, legacy examples,
new state transitions and blocked runtime sockets. There are no publication or
deployment workflows, and the distribution workflow does not trigger on tags.

## Published source and verification

[PR #1](https://github.com/kadubon/observable-agent-workflow-memory/pull/1) and
[PR #2](https://github.com/kadubon/observable-agent-workflow-memory/pull/2) merged
under normal repository policy after every check passed. No protection, review,
security or evidence-admission gate was bypassed.

Release source: `883026e647167bcf74e1baf00600c01870fc5c79`.
Annotated tag: `v0.2.0b0`, peeled to that exact commit.
[Public GitHub prerelease](https://github.com/kadubon/observable-agent-workflow-memory/releases/tag/v0.2.0b0)
was published on 2026-09-21 at 12:17:42 UTC, retaining Beta research status.
This publication record and its JSON evidence are a later documentation change;
they do not change the tagged source or replace any release asset.

- [Merged-source CI](https://github.com/kadubon/observable-agent-workflow-memory/actions/runs/35598172911):
  all nine OS/Python test jobs and selected-fault/security job passed.
- [Exact distribution qualification](https://github.com/kadubon/observable-agent-workflow-memory/actions/runs/35598172994):
  build plus six wheel jobs and one sdist job passed, with separate base/native
  installations in every installation job.
- [Tag CI](https://github.com/kadubon/observable-agent-workflow-memory/actions/runs/35598456295): passed.

The release-source suite contains 116 passing tests. New-profile coverage is
781/796 statements (98.12%) and 246/260 branches (94.62%). Full-suite coverage is
2,172/2,408 statements (90.20%) and 496/632 branches (78.48%). Thirty generated
finite invariant cases and all seven selected faults passed their checks.
Ruff, mypy, schema drift, dependency audit and publication scan passed.

## Public distribution checks

The actual public Release API and all five asset URLs were fetched without
authentication after publication. Every downloaded file matched the qualified
staging bytes; `SHA256SUMS` was checked independently. Distribution SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `observable_agent_workflow_memory-0.2.0b0-py3-none-any.whl` | `acf1319ddce4f857ff507d3fbe58392f1839b2b89d7d3b9af4fc0ec1591d8cbd` |
| `observable_agent_workflow_memory-0.2.0b0.tar.gz` | `aee744395bcf2e7e8dd9b7d3dde6a245d4e26a8818c2fcd606579439c8dc105d` |

Public wheel and sdist were installed separately on Windows/Python 3.13.3 in
four fresh environments outside the checkout, with caches disabled: base and
native integration for each artifact. Literal `pip check`, installed `oawm --help`,
version/import origin, bundled resources, three legacy examples and the new
example passed. Runtime sockets were blocked after dependency acquisition.
Base installations contained neither the optional LLM provider nor companions.
Native checks used ALT 0.5.0 and CCR 1.8.0, pinned to the exact public wheel hashes
and source/schema identities in the release qualification manifest.

The installed new example executes both a correct file-producing operation and
a deliberately faulty local operation. Independent checking blocks future use
after the faulty output; fresh evidence restores eligibility. Receiver B requires
its own qualification, and dependency withdrawal subsequently blocks both while
one historical service and the recorded costs remain. These are synthetic checks.

Machine-readable results, download URLs, hashes, exact commands and sanitized
installation outputs are in
[public-asset-verification-0.2.0b0.json](public-asset-verification-0.2.0b0.json).
The Release's `qualification-manifest.json` retains the earlier cross-platform
installation evidence and full companion pins. Public verification was recorded
after publication without rewriting that manifest or any distribution.

## Delivery statuses

| Status | Result |
| --- | --- |
| IMPLEMENTATION | PASS — M1–M4 finite supported profile |
| LEGACY_COMPATIBILITY | PASS |
| RECEIVER_QUALIFIED_RETRIEVAL | PASS |
| ALT_NATIVE_INTERCHANGE | PASS — ALT 0.5.0 native formation/reconstruction/qualification/selection/checking |
| CCR_TASK_PROPOSAL_CHECK | PASS — CCR 1.8.0 native parser; host admission remains outstanding by design |
| LIFECYCLE_FEEDBACK | PASS |
| TESTS_AND_COVERAGE | PASS — 116 tests; separate new-profile gates met |
| SELECTED_FAULT_TESTS | PASS — 7/7 selected faults detected |
| INSTALLED_ARTIFACT_CHECKS | PASS — 14 CI environments |
| DOCS | PASS — implementation docs and post-publication evidence |
| WIKI | NOT_APPLICABLE — no existing Wiki repository |
| PUSH | PASS |
| PULL_REQUEST | PASS |
| MERGE | PASS — normal policy |
| TAG | PASS — v0.2.0b0 |
| GITHUB_RELEASE | PASS — Beta prerelease |
| PUBLIC_ASSET_INSTALLATION | PASS — public wheel and sdist, four fresh environments |
| PYPI_PUBLICATION | NOT_REQUESTED |
| EXTERNAL_EMPIRICAL_ACCELERATION | NOT_PERFORMED |

No permission or verification barrier remains for this requested delivery.
VEK/CAIT are explicitly partial sidecars, not native integration claims. Native
ALT/CCR acceptance is neither production integration nor execution authorization.

PyPI/TestPyPI, Zenodo and production deployment are **NOT_REQUESTED**. Signatures
and provenance attestations are not claimed; hashes check byte integrity.

No external empirical AI acceleration experiment was performed. Memory exposure,
procedure execution, checked outcome, receiver qualification, modeled economic
benefit, causal attribution and execution authority remain separate. The release
preserves Beta research status and makes no claim of AGI/ASI, universal transfer,
authenticated remote observations or indefinite collective growth.
