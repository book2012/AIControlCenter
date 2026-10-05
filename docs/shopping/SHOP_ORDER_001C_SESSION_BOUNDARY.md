# SHOP_ORDER_001C-B — Session-bound Order Application

## Status and scope

Repository-only isolated application composition on top of canonical product resolution at `caa2ca8`. No HTTP route or production app registration, live writer, credential loader, runtime default, deployment or database migration is added. Validation uses the real CustomerSessionBoundary/CustomerSessionService with synthetic issuance, temporary SQLite and fake catalog/writer only.

## Trust and execution sequence

1. Revalidate the closed browser intent: canonical product/variation references, bounded quantities and idempotency key only.
2. Require exact trusted origin; reject ambiguous cookies.
3. Authenticate the credential through the existing boundary, including current durable session/customer validity, revocation and expiry.
4. Verify the session-bound CSRF token, rejecting missing/duplicate tokens.
5. Derive customer/session identity from the authenticated boundary result. Generate authorization, correlation, audit references and request time on the server.
6. Bound authority to the earlier of idle expiry, absolute expiry and a 30-second operation window.
7. Execute the existing order service: durable claim, trusted catalog resolution, inert writer, bounded result persistence.

A SafeSessionProjection cannot substitute for CustomerSessionBoundary. Its fields are consumed only after credential authentication and CSRF validation. Replay goes through these same checks on every request, including after completion. The existing boundary has a process-local issuance index and is not a production multi-worker/restart session composition; this milestone does not change that limitation.

## Stable operation identity and immutable audit

The command digest contains customer identity, canonical product/variation/quantity intent and idempotency key. Per-request correlation/audit references and request timestamp are excluded from identity so newly authenticated attempts can replay the same intent. The ledger still binds identity to the original session and retains original authorization/correlation/audit/time evidence immutably. Changed intent or another session conflicts; ambiguous outcome cannot invoke the writer again.

This candidate digest change is not a migration of earlier ledger records. An existing record with the prior digest will conflict and remain blocked. There is no production ledger activation or automatic rewrite of prior audit evidence.

## Verification

Initial Order/catalog baseline: 37 passed. Composition exposed two replay failures caused by volatile digest fields; those were corrected. Final combined Order/catalog/read/customer/session regression: **516 passed, 1 existing Starlette/httpx deprecation warning**. The composition adds 26 test cases, including valid durable completion/replay, different-session conflict, changed intent, expired/revoked/unknown credentials, missing or invalid origin/CSRF, duplicate cookies/tokens, storage outage, forged authority/commerce fields, model_construct bypass, unknown-outcome retry blocking and claim-before-writer ordering. Test network access is denied.

## Next milestone

An isolated create-order HTTP route and bounded public error/result mapping can be designed next, with fake writer composition and no production mounting. Live WooCommerce write transport, credentials and all PROD mutations remain separately gated.
