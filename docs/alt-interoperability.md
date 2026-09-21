# Native, version-bound ALT interoperability

The optional development group `integration` installs immutable public GitHub wheels.
OAWM core and legacy examples do not require these packages or any LLM SDK.

| Producer | Version | Commit | Wheel SHA-256 |
| --- | --- | --- | --- |
| ALT | 0.5.0 | `cdb5c7d845364f0bec42ebe5e865871b2bde2e91` | `cd6755db6d97f978300d978695dc70c19d64fdd11c58e0c6dc4c1fcb7db9f487` |
| CCR | 1.8.0 | `1591e88e3b05f9b5fb06b2d0c749aad8bc0909be` | `97b2f3dc1f675c78246c362d211b71452b721b001e25dd2711263f34874f8b25` |

```sh
python -m pip install 'https://github.com/kadubon/alt-foundry-kernel/releases/download/v0.5.0/alt_foundry_kernel-0.5.0-py3-none-any.whl#sha256=cd6755db6d97f978300d978695dc70c19d64fdd11c58e0c6dc4c1fcb7db9f487'
python -m pip install 'https://github.com/kadubon/collective-capability-runtime/releases/download/v1.8.0/collective_capability_runtime-1.8.0-py3-none-any.whl#sha256=97b2f3dc1f675c78246c362d211b71452b721b001e25dd2711263f34874f8b25'
oawm qualified example
```

The packaged `qualified/resources/manifest.json` binds actual companion schema,
documentation, fixture, license and NOTICE bytes by commit/path/SHA-256. Native
schemas resolve only local references. Version mismatches fail explicitly.

`qualified.native.form` maps each registered observation's primitive, argument,
implementation, time, partition, outcome and cost to an actual ALT Formation.
Every output slot has an original event/field mapping. Original source bytes and
their producer digest remain alongside the ALT envelope, not replaced by it.
At least two training episodes must precede the registered cutoff; evaluation
sources cannot be mined. Failed/partial sources cannot qualify. The native ALT
extractor and its independent reconstruction checker both run.

`propose` runs separate finite receiver evaluation evidence through native ALT
qualification. The local reconstruction checker verifies projected slots against
source bytes without invoking the extractor again. Output invariants are recomputed;
an imported passed flag is insufficient. Qualifications bind the exact current
OAWM update and content digest, context, inputs, costs and original observations.
The registered procedure's output correctness is finite and deterministic; this is
host-recorded evidence with unresolved source authentication, not a factual-truth
or economic-value certificate.

Successful read-only proposals return explicit payable cost records. Failed proposals
raise `AttemptError` retaining payable modeled costs and unresolved source obligations.
Hosts record costs through explicit append operations; admission refuses missing or
conflicting physical charges. Failed checks do not silently become free.

`qualified.economics.compare` delegates to ALT's actual selector/comparators and
independent plan checker. The example treats already recorded formation/check costs
as sunk while retaining them in lifecycle costs; additional transfer and use costs
remain explicit. Search exhaustion returns only status and any checked incumbent,
without upgrading feasibility to optimality. The declared finite value scale is not
empirical savings, causal contribution or capability stock.

The pinned ALT-to-CCR importer gap remains: CCR's old ALT token adapter targets 0.4.0.
OAWM does not relabel the stronger sidecar as natively enforced by that importer.
See [collective-handoff.md](collective-handoff.md).
