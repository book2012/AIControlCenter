# DPL-04C Durable Audit Architecture Decision

DPL-04C establishes AIControlCenter and the Mac Control Plane as the owner of
authoritative durable deployment audit. Ubuntu remains stateless and cannot own
audit governance, policy or authoritative state.

`core.deployment.audit_contracts` provides immutable `AuditEvent`,
`AuditEnvelope`, append request and receipt, integrity report, bounded read-only
query contracts and the replaceable `DurableAuditPort`. Canonical JSON, stable
IDs, deterministic digests and previous-hash linkage define semantic identity.
Genesis uses the explicit `GENESIS` previous-hash marker. Verification detects
modified payloads, broken links, reordering, duplicate positions and
deterministically observable gaps.

The future adapter decision is an append-only SQLite ledger on the Mac Control
Plane. SQLite is not the domain model, and DPL-04C implements no adapter,
database, migration, persistent audit or nonce write, API route, background
worker, network access, subprocess call or Ubuntu integration. Audit query
integration remains read-only-first.

Hash chaining supplies tamper evidence, not absolute tamper prevention.
Secrets, credential material, raw environments, executable command data,
unrestricted personal data, production targets and
`production_authorized=true` are rejected. Retention, deletion and compaction
remain prohibited pending separate authorization.

DPL-04A, DPL-04B and DPL-04C are closed. DPL-04D is ready. M2 is not complete,
the persistent audit adapter is not implemented, and production activation is
`NOT_AUTHORIZED`.
