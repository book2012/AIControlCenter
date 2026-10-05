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
## Canonical implementation evidence

- Parent / 001A: `65f39d299e53a9be1687bfe46c71fe8c4787b4e4`.
- 001B implementation: `c6b3e3b1578501d4a9845cf00a5895e29e6da065`.
- Order/read focused regression: **83 passed**.
- Existing customer/session security regression: **244 passed, 1 warning**.
- Python compile check: PASS.
- New create/ledger modules contain no provider HTTP client, WooCommerce write credential, or WooCommerce write endpoint.

README review: no change required because 001B adds no customer-facing route, runtime activation, deployment procedure, or operator workflow.

## Completion persistence and current authority gate

Before a durable claim, the ledger requires `authorized_at <= ledger_clock < expires_at` in addition to the command/authority binding checks. This rejects stale evidence even when the original command timestamp was valid. The later session boundary must still authenticate the caller and check current revocation, origin and CSRF; the internal authority object does not replace those checks.

After a successful provider response, failure to persist COMPLETED is ambiguous. The service attempts UNKNOWN_OUTCOME quarantine and re-raises the original persistence error. If the completion committed before the error, the immutable COMPLETED row remains replayable. If quarantine also fails, the durable CLAIMED row remains blocked; operational reconciliation must establish the outcome before any future write. No automatic provider retry is introduced.

Validation: the initial focused suite passed 25 tests. Three added failure cases were reproduced before correction. The final combined Order/read/customer/session regression passed 483 tests with one existing Starlette/httpx deprecation warning. Five additional tests cover current authority bounds, quarantine after completion failure, post-commit replay, and failure of both completion and quarantine persistence. All writers were fake and ledger databases isolated; no Production mutation occurred.
