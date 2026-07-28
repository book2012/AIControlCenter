# DPL-02D — GET-only API and M1 closure

## Status, lifecycle, and ownership

DPL-02D and the DPL M1 read-only contract milestone are complete. The
AIControlCenter Mac Control Plane owns the API, application composition,
policy interpretation, and audit-evidence generation. A request follows a
strict GET → injected read service → versioned response → audit-ready evidence
lifecycle. No stage activates a package or crosses into an apply boundary.

The API prefix is `/api/deployment/v1`. Its only operations are:

- `GET /schemas` for local DPL contract discovery;
- `GET /packages/inspect` for immutable `dpl/v1` package validation;
- `GET /inventory/mac` for DPL-02B Mac inventory;
- `GET /readiness/ingress` for DPL-02C ingress readiness.

Routes are thin composition adapters. DPL-02A contract validation, DPL-02B
inventory, and DPL-02C readiness semantics remain owned by their existing
application services.

## Response and error contracts

Successful responses use `DeploymentApiResponse`. It identifies the
operation, contains the unchanged capability result, and includes one
`DeploymentAuditEvidence` object. Schema discovery returns stable contract
names, URN schema identities, and versions without filesystem paths. Object
serialization, contract lists, inventory items, checks, evidence references,
and error collections have deterministic ordering.

Malformed packages return the schema-valid `ErrorEnvelope` with a controlled
message and logical `package` path. Partial inventory or ingress observation
failures remain structured `degraded` or `unavailable` results rather than
leaking exceptions. `NOT_READY` is a valid readiness result, not an API
mutation or repair request. Secrets, raw exception text, absolute paths, and
implementation details are excluded.

## Audit evidence and persistence boundary

Evidence records schema version, deterministic event ID, operation,
actor/context/request identities, applicable subject digest, result
classification, injected-clock timestamp, `read_only: true`,
`production_writes: 0`, `ubuntu_changes: 0`, and redacted error metadata.
Tests inject a fixed clock and in-memory sink.

The default sink is intentionally a no-op. DPL-02D does not import or enable a
SQLite or other durable audit repository and performs no persistent audit
write. Connecting evidence to durable persistence requires a separate
operational authorization decision.

## Method denial and read-only guarantee

POST, PUT, PATCH, and DELETE have no DPL handlers. Framework-level 405 denial
occurs before service, adapter, sink, or runtime dependency invocation. No
apply, execute, restart, install, bootstrap, rollback, activation, or mutation
route exists.

Composition uses Mac repository-file parsers only. It imports no Ubuntu
worker, SSH runner, generic command runner, network client, or
mutation-capable runtime executor. It performs no live commands or network
access. Host Caddy remains the sole public edge; WordPress and WooCommerce
remain engines behind it; AIControlCenter retains all business logic.

## DPL-02 and M1 acceptance evidence

- DPL-02A: versioned local-only schemas, canonical JSON, validation, and
  immutable package policy complete.
- DPL-02B: deterministic Mac Control Plane inventory with structured partial
  failures complete.
- DPL-02C: deterministic ingress correlation and readiness classifications
  complete.
- DPL-02D: GET-only composition, method denial, audit-ready evidence, error
  envelopes, and compatibility coverage complete.
- Targeted DPL-02D, all deployment, relevant API/governance, and full
  regression suites pass.
- Production business writes, persistent audit writes, Ubuntu changes,
  network accesses, and runtime commands remain zero.

M1 explicitly excludes activation, apply execution, persistent production
audit, production-generated evidence, live runtime probing, Ubuntu access,
SSH, Caddy reload, Docker/Compose/Colima execution, service restart, and
production writes.

The next task is DPL-03: enforce read/plan/apply package and dependency
separation. M1 completion does not authorize production activation.
