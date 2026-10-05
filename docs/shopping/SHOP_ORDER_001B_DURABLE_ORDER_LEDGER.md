# SHOP_ORDER_001B — Durable Order Operation Ledger

## Status

Repository-only implementation candidate. No provider write or Production
activation is introduced.

## Purpose

001B makes order-create idempotency and ambiguity durable before any future
WooCommerce POST is permitted. The Mac AIControlCenter remains the sole
control plane and durable authority.

## Authority binding

Every create operation is bound immutably to:

- opaque existing CustomerId,
- opaque existing SessionId,
- original server-owned authorization reference and authorization lifetime as immutable audit evidence,
- immutable command digest and idempotency key,
- correlation and audit references,
- request/authorization timestamps.

The idempotency identity is the immutable command digest plus customer and session IDs. A refreshed authorization decision from the same still-authenticated session may replay an already completed operation without a second provider write; a different session or command conflicts. The original authorization reference and timestamps remain immutable evidence.

`OrderCreateAuthority` is an internal contract only. Constructing it is not
authentication. A later API milestone may create it only after the existing
CustomerSessionBoundary has validated session credential, current durable
session state, revocation, expiry, trusted origin and CSRF.

## Durable state machine

`CLAIMED → COMPLETED`

`CLAIMED → TERMINAL_FAILED`

`CLAIMED → UNKNOWN_OUTCOME`

`UNKNOWN_OUTCOME → COMPLETED | TERMINAL_FAILED` only through explicit
reconciliation methods.

Operation identity is immutable and operation/audit deletion is prohibited by
SQLite triggers.

## Unknown outcome rule

Any ambiguous provider/network exception or post-write contract mismatch is
quarantined as UNKNOWN_OUTCOME. It cannot be automatically retried. A future
reconciliation process must establish whether a provider order exists before
the ledger can become completed or terminally failed.

Only an explicit OrderCreateDefinitiveFailure may transition directly to
TERMINAL_FAILED; that exception means the future writer can prove no provider
order was created.

## Persistence

The ledger uses SQLite WAL + synchronous FULL and BEGIN IMMEDIATE for claims
and transitions. The default durable path policy rejects temporary paths, the
Git repository tree and symlink traversal. Unit tests inject an isolated
test-only path policy.

Stored order result JSON is the bounded OrderSnapshot projection. It contains
no billing address, shipping address, email, phone, browser credential, CSRF
token, payment credential or raw provider response.

## Explicit exclusions

001B adds no WooCommerce POST/PUT/PATCH/DELETE, write credential, customer API
route, Agent create-order tool, cart/checkout activation, payment/refund/
fulfillment mutation, WordPress change, Production database creation or
migration, runtime restart, deployment or Production activation.

## Next gate

001C should add a session-bound API/application composition using the existing
CustomerSessionBoundary plus a fake/inert writer first. Only after that should
a separately reviewed WooCommerce write adapter be designed.
