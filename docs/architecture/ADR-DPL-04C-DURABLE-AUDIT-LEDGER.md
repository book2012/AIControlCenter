# ADR-DPL-04C: Durable Deployment Audit Ledger

- Status: Accepted
- Decision date: 2026-07-29
- Scope: Deployment Package Lifecycle durable audit

## Context

Deployment authorization, sandbox execution requests, results and policy
denials need an authoritative history. Ubuntu is an optional stateless
infrastructure worker and cannot own audit governance, policy or authoritative
state. Hash linkage can make changes evident, but cannot prevent an actor with
host-level control from replacing both data and verification code.

## Decision

AIControlCenter owns durable deployment audit on the Mac Control Plane.
Canonical JSON is the authoritative semantic payload format. Events use stable
IDs, explicit timestamps, deterministic SHA-256 digests, monotonic sequence
positions and previous-event hash linkage. The chain provides tamper evidence,
not absolute tamper prevention.

The selected future storage adapter is an append-only SQLite ledger behind the
replaceable `DurableAuditPort`. SQLite is an implementation adapter, not the
audit domain model. DPL-04C defines only pure immutable contracts and the port;
it creates no database, migration or persistent record.

The future adapter must:

- run only on the Mac Control Plane and keep application state outside Git;
- use append-only transactions, WAL mode, `synchronous=FULL`,
  `foreign_keys=ON`, a bounded busy timeout and an explicit schema version;
- enforce unique event IDs and a monotonic ledger sequence;
- preserve immutable canonical payload, previous hash and event hash;
- provide an online backup strategy plus restore and integrity verification;
- expose a read-only query path and remain replaceable at the port boundary;
- never give Ubuntu ownership of audit state or policy.

Secret values, credentials, authorization headers, cookies, raw environment
variables, command data and unrestricted personal data are prohibited.
References, stable IDs and cryptographic digests are used instead.

Retention, deletion and compaction are prohibited until separately authorized.
Production activation is `NOT_AUTHORIZED`.

## Consequences

Future persistence can be added without coupling planning, authorization,
sandbox or API modules to SQLite. Integrity verification detects observable
broken links, modified events, reordering, duplicate sequences and missing
positions. Host-level compromise remains outside the guarantee and requires
separate operational controls.
