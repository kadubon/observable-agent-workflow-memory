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

GitHub publication and public-asset installation remain pending until exact source
SHA, qualification runs, hashes and unauthenticated downloads are recorded here.
PyPI/TestPyPI, Zenodo and production deployment are **NOT_REQUESTED**. Signatures
and provenance attestations are not claimed; hashes check byte integrity.

No external empirical AI acceleration experiment was performed. Memory exposure,
procedure execution, checked outcome, receiver qualification, modeled economic
benefit, causal attribution and execution authority remain separate. The release
preserves Beta research status and makes no claim of AGI/ASI, universal transfer,
authenticated remote observations or indefinite collective growth.
