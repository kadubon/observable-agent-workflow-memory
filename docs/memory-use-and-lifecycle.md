# Checked use and lifecycle feedback

The sidecar log is append-only and versioned independently from legacy schema 1.1.
`Store.initialize()` explicitly adds `receiver_events` beside the legacy tables;
it does not change legacy JSON bytes or mint qualifications. Repeated initialization
is idempotent. The SQL migration is shipped in both distributions.

`ReceiverRuntime.admit` rechecks current promotion, source mapping, native qualification,
host context and lifecycle while holding a SQLite write transaction. It records
physical costs once and admission atomically against an expected journal revision.
The log hash binds recorded order; each event also has separate host-supplied occurrence
time. Replay of a fixed prefix is pure and does not rewrite past reports after late
evidence. `Store`, SQLite and host plugin configuration are trusted local persistence;
editing database files or directly forging low-level log records is outside the host
trust boundary. Import/export does not grant write permission.

Qualified retrieval returns a decision snapshot. Context exposure records `exposure`,
not a service. `use` requires a current qualification, exact input/action, action-bound
passing receipts and an explicit physical use cost. It durably reserves an `intent`,
then rechecks eligibility and holds a SQLite write fence across the supported local
tool call and `attempt`, `outcome`, `checked`, `reconciled` records. The separately
implemented output checker establishes only the registered finite postcondition.
An external effect's ActionIntent ID is recomputed from its fields; changing arguments,
tools or resource caps while retaining an old ID is rejected.

Identical retries cannot create another service or charge. Conflicting IDs fail.
Crashes after reservation retain the cost and unresolved intent, with no phantom
completion. Timeouts/unknown outcomes remain unresolved, distinct from checked
negative outcomes. A renamed retry cannot dispatch the same unresolved qualification
and input. Host review is required for unresolved effects; arbitrary correction of
outcomes is explicitly unsupported. A correction record is rejected rather than
silently rewriting past evidence.

A checked negative result creates an artifact/context/input-specific block. An
explicit host invalidation may also block that scope. Imported allegations are retained
as allegations and do not authenticate a global revocation. Refresh requires a new
qualification with valid-from and receiver-check time later than the block, and new
authoritative observation identities. Old receipt/qualification reuse cannot clear it.
Changing a local memory name does not change the typed artifact identity. Dependency
withdrawal blocks both receivers sharing that exact implementation, without deleting
past outcomes or costs. New dependency implementations require new qualification.

Expiry uses exclusive upper bounds. Supersession/retirement in the legacy authoritative
record immediately blocks new use of that revision. Every decision reloads it.
Read-only replay never mutates legacy receipt meanings. Host clocks, file permissions
and tool sandboxing remain host responsibilities. A SQLite fence serializes tested
local writes; no distributed ordering, cancellation of running external actions,
exactly-once external execution or remote tenant isolation is claimed.
