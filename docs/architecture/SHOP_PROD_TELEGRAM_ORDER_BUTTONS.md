# PROD Telegram order controls

## Scope

The production operator bot is `mommychichi_bot`. It uses the PROD commerce API, WooCommerce site, private order ledger, cursor and aftersales database. The DEV operator bot and its papachichi credentials, cursor and storage are not composed into this runtime.

Telegram order requests are sent as one message per order. Each card shows the 10-digit public order number, customer/order details, the price on its own line, the latest status-change time, and only actions valid for its displayed status. Detail, confirm, payment, shipping, delivery and pre-shipment cancellation callbacks are bound to the exact PROD bot message, configured private chat and allowlisted operator.

The order list starts with a choice of all orders or a status. Cancelled orders are excluded from all orders and remain visible in the cancellation-complete filter. A callback acknowledgement and its result reply name the selected button and order number to distinguish it from earlier commands.

## Production cancellation boundary

The cancellation provider calls `assert_production()` for every apply/reconcile operation, checks the production Colima context, `shopping-wordpress` container and `aicc_shopping` database, and binds the Woo order to the internal operation tag, delivery digest and complete line-item set. It restores only verified reduced stock, records an idempotent cancellation receipt, and sets Woo status to cancelled. It suppresses Woo email hooks. It does not issue payment refunds. Unknown outcomes require read-only reconciliation; commands are not automatically replayed.

## Audit history

The PROD aftersales SQLite store records payment, fulfillment, cancellation, case, return-stock and refund state changes in append-only `order_status_history`. Each entry has an event key and timestamp. Existing status transitions are not backfilled; timestamps begin recording when the schema is installed. Older orders show their known receipt time until a new transition is recorded. Order details and cards display the recorded timeline/latest change where available.

## Verification and rollout

Tests use temporary databases and stub providers. They must not call WooCommerce or mutate real orders. On deployment, the PROD service performs an additive SQLite schema initialization, starts one existing PROD bot poller, and is checked through its local health endpoint. No order is used as a live test.
