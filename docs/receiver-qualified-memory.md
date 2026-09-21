# Receiver-qualified memory (0.2.0b0, Beta)

The opt-in `qualified` profile adds a local, finite reuse path. Legacy schema 1.1,
memory lanes, identifiers, receipts and APIs retain their meanings. In particular,
legacy `AgentKernel.run` USE telemetry denotes memory placed in context, not an
independently observed procedure execution. Legacy certification alone does not
admit a receiver qualification.

The host explicitly registers at most eight `Context` records with workspace,
receiver, mission, family, context, finite inputs, clock, tool/protocol/evaluator,
required checks, dependency hashes, effect restrictions and exposure policy.
Contexts come from host configuration, never imported memory instructions.
Receivers are local policy subjects; this is not remote authentication or tenant
isolation. Time is an explicit trusted host integer; validity is `[start, expiry)`.

`ReceiverRuntime.retrieve` evaluates every admitted candidate within the bounded
store before ranking. It reloads the current memory, promotion receipt, workflow,
manifest and original event bytes; repeats legacy binding checks and native ALT
source reconstruction; checks exact receiver/input policy, costs and lifecycle.
Custom retriever content and lane labels are not used by this path. Missing
premises block eligibility, malformed records raise errors, and absent optional
runtime dependencies produce actionable errors. No empty named checker set passes.

`AgentKernel.run_qualified(..., receiver_runtime=..., receiver=..., input_text=...,
now=...)` connects these decisions to actual model context, recording only exposure.
`ReceiverRuntime.use` is a separate strict local execution boundary. Eligibility is
not execution permission. The independent `qualified.checker.check_view` reconstructs
an eligible view against current authoritative state without calling retrieval or
its decision function.

The first finite language is one explicitly registered `normalize-lines-v1`
primitive: bounded text becomes sorted unique lines joined with LF. Its actual
implementation source bytes have a digest, and a separately implemented invariant
checker verifies the output. No prose is converted to code. Arbitrary plugins,
shell strings, paths, URLs and serialized programs are not executed from memory.

Bounds: 2 MB JSON/journal, depth 24, 50,000 traversal nodes, 256 journal entries,
eight training and eight evaluation sources, eight receivers, eight dependencies,
eight exact inputs per context, 4,096 characters per input, and 32 returned views.
Each source has a distinct observation ID, original UTF-8 bytes, envelope SHA-256
and separate producer digest. Exact nonnegative rational cost strings have at most
128-bit numerator/denominator. Booleans are not integer clocks or quantities.
Unsupported versions/fields, duplicate keys, resource exhaustion and missing
dependencies fail closed. No remote schema resolution occurs.

## Installed quickstart

Download the wheel and SHA256SUMS from the GitHub prerelease and verify the hash
before installing the wheel into a virtual environment. ALT is distributed by
GitHub, not assumed to be on PyPI. Install the exact companion wheels listed in
[alt-interoperability.md](alt-interoperability.md) for the new example.

```sh
oawm --help
oawm qualified resources
oawm qualified example
```

The example creates temporary local state and a real result file, uses the existing
action-bound gate, verifies the result, demonstrates scoped failure/refresh and
shared withdrawal, and removes the temporary directory. Runtime sockets are blocked;
there are no real LLM calls. It compares only finite context exposure counts and
declared model costs: no memory exposes zero records, legacy retrieval exposes the
certified record, A can retrieve the qualified record, and initially unsupported B
cannot. Separate B evidence enables B. High transfer cost makes native ALT choose
scratch while technical eligibility remains true.

For an existing initialized profile database and explicit JSON list of host Contexts:

```sh
oawm qualified inspect state.sqlite
oawm qualified retrieve state.sqlite host-contexts.json A 'b\na\nb' 4
oawm qualified check qualification.json 4
oawm qualified export qualification.json
```

The input argument must contain the actual intended text (the quoted `\n` notation
above must be expanded by the caller). Inspection/retrieval/check/export write no
database or filesystem state and never initialize storage. Active WAL state causes
read-only inspection to refuse rather than ignore newer evidence; use a transaction
snapshot or checkpoint first. Exit zero means a valid report, not necessarily
eligible memory. Reports preserve source authentication, semantic scope, eligibility,
search completeness, residuals and unknown authority separately.

See [memory-use-and-lifecycle.md](memory-use-and-lifecycle.md) for write boundaries,
[collective-handoff.md](collective-handoff.md) for host admission, and
[publication-0.2.0b0.md](publication-0.2.0b0.md) for delivery evidence.
