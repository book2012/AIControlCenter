# DEV stock confirmation and operator-assisted inquiry automation

## Architecture and boundaries
AIControlCenter on Mac owns confirmation, operator authorization, inquiry routing and FAQ approval. WooCommerce remains the commerce/stock engine. Composition is explicitly isolated DEV only; no production activation, payment or fulfillment. The original dirty main checkout is untouched.

## Order confirmation and inventory
Customer confirmation creates an unpaid pending Woo order. An allowlisted Telegram operator confirms it. The ledger invokes an explicit stock guard before committing CONFIRMED, audit, notification and Telegram cursor together. Insufficient stock, binding errors or unknown receipts leave review pending and enqueue STOCK_BLOCKED; the operator inspects/retries the same order, never creates a new order.

The DEV adapter verifies Docker project/volume isolation, database identity, operation metadata, private delivery digest and exact item IDs/quantities. It uses a global MySQL advisory lock and an InnoDB transaction, checks all remaining quantities before reducing, calls native Woo stock functions, verifies line reduction metadata, persists the order reduction flag and changes pending to on-hold. Email is suppressed. The transaction commits stock, line/order flags and status together. Replays use the same order and flags, including after a lost response; no manual quantity overwrite or blind stock decrement. Each confirmation is bounded and refuses unsupported storage engines.

Stock may commit before the local ledger transaction; after a local crash the same trusted update/order is safe to retry against Woo flags. Unknown provider receipts never become confirmed. The lock coordinates this adapter's confirmations; production would require every stock writer, reservation/cancellation/refund integration, supervised services and a reviewed provider adapter. Generic legacy Telegram integrations do not acquire stock mutation authority by default. Older synthetic fixtures without private checkout binding are not eligible.

Actual DEV order #15, previously operator-confirmed, was explicitly reconciled once: option S changed 20 → 19, and an exact replay remained 19. Option M remains 20 and L remains 0/out of stock. No new order was created, and order #14 remains the old synthetic fixture.

## Telegram conversational commands
The private fixed operator chat/user allowlist remains mandatory. Notifications resolve the phone from the integrity-checked private verified checkout, never caller-supplied identity or a public outbox field.
- Notification: `01012345678 고객님 주문`, product/option/quantity/amount/order number.
- Confirm: `01012345678 고객 주문확인` (also 주문확정).
- Reject/status: `01012345678 고객 주문거절` / `01012345678 고객 주문상태`.
- Multiple candidate orders: `01012345678 고객 주문확인 #15`. No automatic guess.
- Old reference-based commands remain compatible. Duplicate updates do not re-run effects or send informational replies again.
Confirmed order cancellation/restocking is a separate future authorized workflow, not an interpretation of 주문거절. Confirmation is stock allocation, not payment or shipping.

## Inquiry escalation and approved learning loop
Local AI continues to judge basic inquiry intent; trusted catalog facts provide current stock/count/price/description. Shipping, exchange, returns, refunds, defects, customization or mixed policy questions conservatively require operator review. AI failure also escalates.

Unanswered inquiries enter private `inquiries.sqlite3` and a claimed-before-send Telegram delivery state. Delivery uncertainty is blocked, never automatically re-sent. Public responses carry an unpredictable one-day inquiry status capability; raw question/identity is not returned by the status route. The browser polls for up to ten minutes and retains a manual 답변 확인 button on the open page for delayed replies within the one-day capability lifetime; it shows the operator answer without HTML execution. Global DEV admission limits are 10/minute and 100/day.

Telegram:
- `문의 #3eddd1bb 답변 검토한 답변내용` delivers the answer to the waiting customer's page.
- `문의 #3eddd1bb 학습승인` approves that answer for the same normalized question and product, for 30 days.
- `문의 #3eddd1bb 학습제외` revokes automatic reuse.

Answers are candidates until explicit operator approval. Revised answers invalidate earlier approval. Dynamic stock/price responses are never replaced by FAQ policy text. Known phone/email/URL/address patterns are redacted; contact-bearing answers and authentication/payment/order-confirmation text are rejected. Pattern detection is not complete PII detection: the operator must review names, unusual addresses and policy correctness before 학습승인. The UI tells guests not to put personal details in inquiry text.

Approved, sanitized examples are exported privately as `inquiry-learning.jsonl` (0600) after operator commands. This is an auditable FAQ dataset and exact-question reuse, not automatic model weight training, semantic paraphrase matching or a production policy release. Model fine tuning/evaluation, stronger PII review, retention/deletion and production activation remain separate milestones.

## Validation
- 862 scoped order/identity/session/provider/guest regression tests passed.
- 62 focused stock/Telegram/escalation/approval/FAQ tests passed.
- Isolated real Chrome guest phone/shipping/order/operator flow passed, exactly one fake writer and two fake messages, no external provider calls.
- A delayed inquiry concurrency regression proved that Local AI/operator inquiry work no longer suppresses phone verification: inquiry uses an independent read-only UI lock while phone/checkout writes retain the existing serialized write lock. Isolated Chrome observed phone `start` and `verify`, one writer call and two Telegram messages with zero external provider calls.
- Real DEV Woo order #15 stock decrement and idempotent replay passed; live Local AI reports S19/M20/L0.
- Actual escalation example #3eddd1bb was delivered to the existing private Telegram operator chat (message #12 SENT). Human policy reply/approval is pending; it is not claimed as a real completed learning approval.
- A broad legacy suite exposed pre-existing inquiry API directory/bootstrap failures. Representative failures were reproduced unchanged in the prior guest-phone checkout. Those unrelated failures are documented, not counted as current feature passes. Current scoped regression has no failures.
- Python/JS syntax, diff whitespace, secret scan and private SQLite integrity backups checked before task-only commit/push.

Private keys, verified contact, shipping, runtime databases and learning exports remain outside Git. PROD is unchanged.
