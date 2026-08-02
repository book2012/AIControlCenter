# SHOP-03A Controlled Commerce Write Architecture

SHOP-03A is architecture-complete. It provides deterministic orchestration for an approved immutable ProductDraft revision, but performs no WooCommerce mutation. The only write-port adapter is an isolated, instance-local `FAKE`/`DRY_RUN` adapter. A real WooCommerce adapter is `NOT_IMPLEMENTED`, and production writes are `NOT_AUTHORIZED`.

## Inventory and preserved contracts

ProductDraft 1.0.0 stores immutable revision identity, lifecycle state, source observation, proposed fields, validation, exact-revision HUMAN decision, and a non-executable deployment intent. Lifecycle transitions are closed and pure. Validation application results bind a canonical input digest to a revision; review application results bind HUMAN APPROVE/REJECT/REVOKE decisions, authorization/audit references, correlation IDs, and instance-local idempotency.

The unchanged deployment-intent v1.0.0 contract contains `intent_id`, exact draft/revision IDs, target adapter reference, expected source digest, idempotency/authorization/audit references, readiness, actor, correlation ID, and UTC creation time. SHOP-03A wraps that contract in an immutable application representation which also binds the expected revision number, supported `UPDATE_PRODUCT` operation, target product identifier, and proposed-field payload digest. It does not change the schema.

`SourceSnapshotReference` binds the WooCommerce source product identifier, optional snapshot reference, optional SHA-256 digest, and caller-observed UTC time. Controlled-write eligibility requires a digest and compares it exactly. Freshness is evaluated against an explicit non-negative maximum age and caller-supplied UTC `evaluated_at`; there is no hidden clock.

Existing authorization conventions are replaceable and deny-by-default, with exact resource and timestamp binding. Existing idempotency conventions are canonical-digest keyed and instance-local. Generic deployment architecture demonstrates immutable plans, ports, deterministic digests, and adapter separation; SHOP-03A reuses those architectural patterns without importing infrastructure deployment or routing Shopping logic through a worker or remote command.

## Controlled boundary

The service evaluates stable eligibility rejection reasons, obtains an exact ALLOW decision, constructs an immutable controlled plan, checks successful-plan idempotency, and invokes only the injected controlled-plan port. Ineligible and denied attempts are not stored as successful idempotency records. Reuse of a key with another plan returns a typed conflict. Results and previews contain references, digests, decisions, timestamps, and fake identifiers only; they contain no domain aggregate, credentials, or policy internals.

There is no API mutation route, persistent write queue, database, filesystem writer, network client, background worker, Ubuntu dependency, or production activation. SHOP-03B requires separate explicit architecture and authorization.
