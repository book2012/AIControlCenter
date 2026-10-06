# DEV customer after-sales portal and fulfillment workflow

## Scope
DEV now has a phone-authenticated customer portal at `/dev-order/my-orders` and an operator after-sales workflow. This is isolated DEV only. It does not perform payment refunds, carrier API calls, real shipment booking, or production fulfillment.

## Customer flow
The customer reuses the existing phone verification and durable customer session. Only orders owned by that authenticated customer are returned. Return and size-exchange actions are disabled until the operator records `DELIVERED`. Eligibility starts at the recorded delivery-complete timestamp and closes after 14 days.

A request creates a private case in `aftersales.sqlite3`. `RETURN` captures a reason. `SIZE_EXCHANGE` additionally requires a currently available alternative variation; the request does not reserve stock and approval must re-check inventory before any future fulfillment implementation.

Customers can attach up to five JPEG/PNG/WebP images, 5 MiB each. Attachments are streamed with a hard size bound, validated by content signature, renamed to server-generated identifiers, stored outside Git in a 0700 directory, and written 0600. Original filenames are not persisted.

## Operator flow
The allowlisted Telegram operator can use:
- `주문발송 #16 CJ대한통운 1234567890`
- `배송상태 #16`
- `배송완료 #16`
- `환불목록` / `교환목록`
- `환불승인 #케이스번호` / `환불거절 #케이스번호`
- `교환승인 #케이스번호` / `교환거절 #케이스번호`

These commands are update-idempotent. Shipment recording is internal DEV state only; it does not call a carrier. Return approval becomes `RETURN_APPROVED`; exchange approval becomes `EXCHANGE_APPROVED`. Neither state claims money was refunded or a replacement was shipped.

## Admin console
`/dev-order/admin` now shows current delivery state and an after-sales case list in addition to orders, addresses and inquiry learning. The admin console remains read-only in this release. Delivery address remains absent from the order-list API and is only returned by the explicit order-detail route.

## State rules
Fulfillment: `NOT_SHIPPED -> SHIPPED -> DELIVERED`.

After-sales: `REQUESTED -> RETURN_APPROVED | EXCHANGE_APPROVED | REJECTED`.

A new case is denied when the order is not operator-confirmed, delivery is not complete, the delivery-complete timestamp is outside the 14-day window, the order is not owned by the authenticated customer, or another active case already exists.

## Validation
- New after-sales focused tests: 4 passed.
- Combined guest/operator/admin/after-sales focused regression: 54 passed.
- Existing isolated real Chrome guest order flow passed with one fake writer, two fake Telegram messages, no external provider requests and no PROD mutation.
- Live DEV smoke: poller RUNNING; customer portal served; unauthenticated order API returned 401; admin after-sales UI served; existing orders #16/#15 remained NOT_SHIPPED; case count 0.
- Private runtime state permissions verified: aftersales SQLite 0600, attachment directory 0700.

## Remaining gates
Actual money refunds require an explicit payment-provider adapter and reconciliation contract. Carrier booking/tracking requires a reviewed carrier adapter. Exchange approval does not yet reserve/restock/ship inventory. Admin write controls and Telegram inline buttons are the next operator-UX milestone. PROD remains unchanged.
