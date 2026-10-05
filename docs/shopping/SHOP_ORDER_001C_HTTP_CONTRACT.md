# SHOP_ORDER_001C-C — Isolated Order Create HTTP Contract

## Status and composition

Repository-only, unregistered router. An isolated FastAPI application may include `core.api.routes.order_create.router` and explicitly override `get_order_create_application` with the session-bound application from 001C-B. The default dependency fails closed with 503. The production app remains unchanged. Tests compose the real customer-session service/boundary, isolated SQLite, fake catalog and fake writer. There is no live provider writer, credential, deployment or production database operation.

## Request

`POST /shopping/orders` accepts only `line_items` and `idempotency_key`. Each line has a bounded canonical string `product_id`, optional canonical string `variation_id`, and a strict integer quantity from 1 to 1000. There must be 1–100 lines, with no duplicate product/variation identity. Client customer/session identity, authorization, timestamps, audit references, prices, totals, contact/billing/payment data are rejected.

The route bounds actual streamed request bytes to 32768 before FastAPI parsing, including requests with absent or dishonest Content-Length. Exact trusted origin, browser credential, current durable session/customer validity and session-bound CSRF remain mandatory. There is no runtime default or cookie-only bypass. The slash variant is handled locally without a redirect.

## Public response

A completed result exposes only `outcome=COMPLETED`, positive `provider_order_id`, bounded `status`, `currency`, decimal-string `total` and `total_tax`, and `idempotent_replay`. Internal customer/session identifiers, authorization, command digest, correlation/audit evidence, raw provider output and credentials remain private.

| HTTP | Outcome |
| --- | --- |
| 201 | First completed operation |
| 200 | Authenticated same-session completed replay |
| 401 | Invalid, expired or revoked session; secure cookie cleared |
| 403 | Origin or CSRF denied |
| 409 | Conflicting intent/session, already claimed, unknown outcome or prior terminal failure |
| 422 | Malformed/closed request, catalog rejection or definitive provider rejection |
| 413 | Actual body exceeds 32768 bytes |
| 405 | Unsupported method; Allow: POST |
| 503 | Missing composition or unavailable session/ledger storage |
| 500 | Unexpected or response-projection failure, details redacted |

Errors use a bounded `{detail: {code, message}}` allowlist with `order_create_` code prefix. No exception text or request validation input is serialized. Successful, validation, dependency, method and error responses use `Cache-Control: no-store`. No CSRF response header or CORS allowance is introduced.

## Replay and uncertainty

Same-session replay rechecks current authentication/origin/CSRF before accessing the durable result. A different command or session conflicts. Writer ambiguity and post-write contract mismatch return 409 unknown_outcome. An unexpected writer exception returns a redacted 500 while the service persists UNKNOWN_OUTCOME; a subsequent attempt returns 409 without another writer call. A completion persistence outage may return 503 while the existing ledger safety rules retain COMPLETED, UNKNOWN_OUTCOME or blocked CLAIMED state. HTTP failures are not authorization for automatic provider retries. Explicit reconciliation remains required for uncertain outcomes.

## Verification

41 isolated HTTP test cases cover 201/200 replay, closed and malformed payloads, strict quantities, auth/origin/CSRF failures and duplicate cookies/tokens, secure cookie clearing, changed intent conflict, unknown/definitive/unclassified writer errors, post-write mismatch, in-flight operations, catalog rejection, ledger outage, all unsupported methods, slash behavior, absent default composition, absent production registration and actual/chunked body limits. External network access is denied by test fixtures.

Combined Order HTTP/application/catalog/ledger/read/customer/session regression: **557 passed, 1 existing Starlette/httpx dependency deprecation warning**. No production runtime verification is claimed because this router is not activated.

## Next gate

Review the provider write-adapter contract and durable reconciliation evidence requirements before implementing a live transport. Production session composition, credential scope, provider write authorization and any deployment remain separate gates. The current fake-writer HTTP contract must not be mounted in production as an activation shortcut.
