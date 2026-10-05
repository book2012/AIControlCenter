# SHOP_ORDER_001D — DEV order, operator review and notification candidate

Date: 2026-10-06 (Asia/Seoul). Base: `8b423a467164e1f6946c3ba77e7d669916a686ff`.
Branch: `feature/shop-order-001d-readiness`.

## Implemented flow

The Mac Control Plane authenticates the customer session, origin and CSRF, resolves canonical WooCommerce catalog intent, commits a durable operation claim, and consumes a second immutable provider-dispatch record before HTTP. An explicit scoped WooCommerce adapter creates only an unpaid pending order. The resulting operation, operator-review record and notification outbox event commit atomically.

A fixed-recipient Telegram adapter claims an event durably before sending. It verifies the positive message receipt and exact chat. An explicitly allowlisted human operator may use `/order_status`, `/order_confirm` or `/order_reject` with the 24-character operation reference. Review decision, audit, follow-up notification and monotonic update cursor commit atomically. Confirmation means local operator review; it does not mark an order paid, change WooCommerce status, charge, refund or fulfill.

The authenticated owner can read `GET /shopping/orders/operations/{idempotency_key}`. Other customers/sessions receive not-found. Customer identity, credentials and raw provider data are excluded from the public status projection.

## Durable uncertainty

The operation binds immutable customer/session/digest evidence. Browser sessionStorage persists only nonsecret intent/key/terminal state before POST. Double clicks and reloads do not generate automatic POST retries. Pending or unknown intent cannot be replaced; known terminal state requires an explicit new-order action.

Every unproven result after a WooCommerce POST attempt is ambiguous. No second dispatch is allowed. Exact-order GET reconciliation requires matching order ID, customer, unique hashed operation metadata, command digest and numeric line items; a 404 is not proof of absence. Notifications that crash after claim or have uncertain delivery are blocked and never automatically resent. This deliberately avoids duplicate orders/messages; operator reconciliation procedures remain a live-readiness prerequisite.

## Explicit schema migration

SQLite schema version 2 adds provider dispatch, operator review, notification outbox and Telegram cursor tables plus immutable/monotonic triggers. `initialize()` rejects version 1. Only explicit `migrate_v1()` upgrades an exact validated v1 baseline, inside one transaction. Existing identity/audit and uncertain operations are preserved. Completed result digest and full operation/result binding must validate; failed migration rolls back the added schema and keeps version 1. Completed historical records gain pending review and notification events: inspect their count before enabling any dispatcher. No actual persistent DEV/PROD database has been migrated by this work.

## UI and composition

WordPress detail presentation adds primary **주문하기**, quantity, status and explicit new-order controls. Product inquiry remains a separate form. The order button is disabled by default; only an explicitly supplied DEV capability enables it. WordPress owns presentation, not provider/business authority. The isolated `create_order_dev_app` requires injected session, catalog, ledger, writer and Telegram integration; it registers no public operator endpoint or dispatch endpoint and does not mount itself into the platform.

The existing generic Telegram bot/poller is unchanged. A dedicated fixed-recipient order adapter avoids mutable reply-chat state and generic Control Plane commands. No real bot token, recipient, provider customer mapping or write policy has been activated. Trusted policy and customer mapping are mandatory injections; constructing a permit is not authorization.

## Validation

- Prior combined Python regression: 689 passed, 20 existing deprecation warnings.
- Final current-scope regression: **645 passed, 20 existing warnings**, across 25 files listed in `SHOP_ORDER_001D_VALIDATION.json`. This selected run is distinct from the earlier 689-case run.
- Browser-controller Node tests: 12 passed.
- PHP entrypoint and detail renderer lint: passed using preview-container PHP via stdin, without WordPress bootstrap or database writes.
- Real Chrome 154 CDP test: UI → authenticated HTTP → durable ledger → fake Telegram notification → allowed operator confirmation → owner status passed; one fake provider create, two fake messages, zero external provider calls.
- `--dump-dom` timed out even on an empty page on this remote Mac. The harness now uses bounded CDP evaluation, loopback-only test/CDP ports, a disposable profile and explicit owned-process cleanup. Test-only operator routes live solely in the harness.
- Core-to-ops architecture regression fixed by moving the unchanged Twilio secret-composition implementation into Core and retaining the ops compatibility re-export. Existing callers retain class/function identity.

## Public storefront observation

Read-only evidence on 2026-10-05 for **bokstory.duckdns.org**:

- Public catalog contained five `mock-*` products, all with null image URLs.
- Hero image returned HTTP 200. All 121 packaged media assets matched the deployed manifest hashes (120 product assets plus hero).
- Presentation media mapping accepted only demo `oc-demo-*` catalog identifiers. The five mock catalog products therefore could not use those fashion assets.
- Public product detail still presented product inquiry. Effective public shopping ingress allowed only catalog GET routes; order, inquiry and customer-session routes were blocked.

Media-file deployment was complete, while catalog/media mapping and order-runtime promotion were incomplete. WooCommerce DB migration status was not established by these observations. Do not substitute fashion photos for unrelated mock products.

## Remaining live-readiness gate

1. Supply isolated DEV customer verifier/session composition, canonical Woo catalog and provider customer mapping, governed one-operation write policy and scoped DEV credentials.
2. Select an order bot with fixed operator chat and explicit human user IDs; verify its poller ownership and ensure no competing getUpdates consumer.
3. Inspect/backup an isolated DEV database, explicitly dry-run version migration and uncertainty recovery; enable a supervised dispatcher/poller through explicit DEV composition.
4. Validate real DEV auth → order → Telegram → operator → customer status using a controlled test order. Complete denied-operator, response-loss, restart and delivery-reconciliation checks.
5. Establish the correct catalog/image mapping in DEV, validate visual parity, then prepare immutable release/rollback evidence for a separately authorized promotion to bokstory.duckdns.org.

This commit is repository implementation and isolated validation. It is not live DEV deployment, real Telegram delivery, production migration, or production activation. PROD mutation remains prohibited.

Architecture regression note: the historical SHOP-02A test banned every Shopping POST even though unchanged baseline inquiry routes already used POST. The check now parses actual product-draft route declarations and requires all draft routes to remain GET-only; the immutable historical inventory is preserved.
