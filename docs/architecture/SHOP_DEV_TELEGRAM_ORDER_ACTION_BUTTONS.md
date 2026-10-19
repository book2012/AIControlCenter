## Dedicated cancellation category

The all-orders view and ordinary new-order notifications do not show a cancel
button. The one-screen order selector has a dedicated 주문 취소 category. Its
query includes only pre-shipment orders whose cancellation preconditions are
currently satisfied. Each result card carries an internal-to-the-workflow
visible category marker; callback validation requires that marker and the
matching order row before forwarding the command. This also rejects stale
cancel buttons from older all-orders and notification messages.

Cancellation supports both 확인대기 and 확인완료 review states. For an
unconfirmed Woo order it requires pending provider status and no stock
reduction. For a confirmed order it verifies the stock receipt and restores
stock through the isolated DEV provider. Payment and shipment guards remain in
force.

## Timestamped status history

Order detail combines immutable order-ledger confirmation/rejection audit
entries with append-only after-sales status events. Database triggers record
payment, shipment, delivery, cancellation, return/exchange case, return-stock,
and manual refund transitions with their timestamps. The order list also shows
the most recent recorded state-change time. Historical after-sales transitions
before this history table was deployed are not inferred; new transitions are
recorded from activation onward.

## DEV API command routing

Phone-bound commands emitted by per-order Telegram callbacks must be recognized
by the bridge's deterministic-command allowlist before conversational intent
handling. The allowlist is deliberately limited to supported callback forms
(주문 확인, 주문 상세, 주문 취소, 입금 확인, and shipping actions) with
a domestic phone identifier and a numeric public order ID. This preserves the
existing adapter's identity, state, stock, replay, and cancellation checks.
Natural-language messages continue through the conversational handler.

Regression coverage uses a fake ledger and verifies both paths. It does not
replay a live callback or mutate a real order. After a DEV API release, verify
with read-only order detail before asking an operator to use a newly displayed
button.

# DEV Papachichi inline order buttons

## Scope

This update is for the operator-only `papachichi_bot` DEV consumer. It does not
change the production `mommychichi_bot`, PROD order state, or the separate
customer-facing bot. The DEV order API remains the authority for order state.

## Operator experience

A pending-order reply receives inline **주문 확인**, **주문 상세**, and **주문 취소** actions. The actions dispatch to the existing DEV operator bridge with the displayed 10-digit public order number and phone. Confirmation retains the stock check and duplicate/update protections; detail is read-only; cancellation remains subject to the DEV API's current state and refund guards.

Every order row in a `주문목록` reply receives its own **상세** button. The row also receives **주문 확인** while `확인대기`, and **주문 취소** only for the allowed pre-shipment states `확인대기`, `확인완료`, and `입금대기`. Callbacks must match an order identifier in the exact source message. Unrelated text and unsupported order states receive no action buttons.

## Callback validation

The button callback is accepted only when it comes from the configured private
operator chat and allowlisted human Telegram user, and its source message was
sent by `papachichi_bot`. The callback contains only the 10-digit public order
number. The bot extracts the phone/order pair from that source message and
requires the callback order number to match it before forwarding a deterministic
command. Arbitrary callback text never becomes a command.

The poller explicitly requests both Telegram `message` and `callback_query`
updates. It acknowledges the callback promptly, retains its durable cursor, and
uses the existing bridge's update ID to prevent replay after uncertain handling.
When a result is uncertain, the bot asks the operator to inspect current order
status instead of re-running the mutation.

## Verification and release boundary

Focused fake-provider tests cover keyboard rendering, callback identity and
order binding, bridge dispatch, cursor advancement, Telegram reply markup,
callback acknowledgement, and accepted update types. No Telegram API call,
SMS, real customer action, WooCommerce mutation, or PROD access is part of the
test suite.

The code is published only as a commit-addressed DEV bot release and the
Papachichi launch agent is restarted on that release. The DEV order API and its
database are not migrated or restarted for this feature. The old bot runtime
and launch-agent file are retained for rollback.


## 2026-10-19 callback recovery

The callback acknowledgement and operator bridge dispatch now use separate error handling. The bot logs only sanitized exception types, preserves single-dispatch behavior, and never retries after uncertain command/result delivery. Regression coverage includes acknowledgement failure, bridge failure and result-send failure. See `SHOP_DEV_ORDER_LOOKUP_CALLBACK_RECOVERY.md` for the DEV rollout and order-preservation checks.


## 2026-10-19 DEV admin menu

Sending `메뉴`, `/menu`, `/start`, or `/help` to the private DEV `papachichi_bot` chat returns an inline keyboard for order list, order-lookup guidance, product list, inventory, and product-registration guidance. Button callbacks are accepted only from the configured operator in the configured private chat and only on the bot's own DEV menu message. Product registration remains an instruction/draft flow; the menu does not directly create or mutate a product.

The callbacks dispatch existing read/help commands through the DEV operator bridge, preserving update idempotency. Tests use a fake Telegram transport and do not send a live message or change orders/products.

## Per-order buttons and paged order browser

The private DEV Papachichi order browser shows **전체 보기** and every
supported status filter on the first order-list keyboard. The statuses cover
pending review, deposit, shipping, completion, return/refund, cancellation,
rejection, and stock review. Selecting 전체 보기 queries the latest available
order state. Results
are paged at five orders per page. Each order is delivered as a separate
Telegram message, followed by a next-page control when more results remain.
Messages are paced to avoid flooding the operator chat. The bot also splits
markerless list replies into one message per detected order, so pagination
metadata cannot cause multiple orders to inherit the first order's buttons.

Each order card has its own inline keyboard. Detail is read-only. Confirmation
is offered for `확인대기`; deposit confirmation for `입금대기`; shipping
registration for `배송준비`; delivery completion for `배송중`; cancellation is
shown only for the allowed pre-shipment states. Each callback is checked against
the exact bot-authored source card and the existing DEV operator bridge/API
continues to enforce current state, idempotency, and cancellation/refund guards.

Fake-transport regressions cover cards, pagination, state filters, callback
identity, and cursor handling. No real Telegram callback or order mutation was
used during these tests.

## Numeric and phone lookup input

A bare domestic mobile number (`010xxxxxxxx` or `010-xxxx-xxxx`) returns all
orders for that phone number in one response. A bare 10-to-18-digit number
that does not match the mobile-number format is treated as an order identifier
and opens its detail response. An explicit phone-number order-list command
continues to work. This preserves phone/order disambiguation for the Telegram
operator bridge.

## 2026-10-20 DEV bot/API release alignment

The callback bot and order API must run compatible immutable releases because
menu, page, and status-filter callbacks are resolved by the API's DEV operator
bridge. A bot-only rollout can leave a newer callback command unrecognized by
an older API runtime and route it into the conversational handler. After
callbacks timed out, the bridge ledger was checked for incomplete operations;
all were complete. The API and bot were then restarted on the same immutable
release without a database migration. Read-only bridge checks returned the menu
and a current order page quickly. PROD remains unchanged.

## Typed order-list command and bridge response validation

Typing `주문목록` or `주문 목록` opens the one-screen selector; explicit
`주문목록 N` remains available for a limited list lookup. DEV bridge responses
include the authenticated `[개발]` header, so the bot strips that exact header
when matching selector/navigation messages and validating those callbacks. Tests
cover the actual prefixed selector and navigation message shape.
