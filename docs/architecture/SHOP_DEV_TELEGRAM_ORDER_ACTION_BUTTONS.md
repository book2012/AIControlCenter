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

The private DEV Papachichi order browser starts with **전체 보기** and
**상태별 보기**. Status choices cover pending review, deposit, shipping,
completion, return/refund, cancellation, rejection, and stock review. Results
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
