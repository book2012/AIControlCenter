# DEV Papachichi inline order buttons

## Scope

This update is for the operator-only `papachichi_bot` DEV consumer. It does not
change the production `mommychichi_bot`, PROD order state, or the separate
customer-facing bot. The DEV order API remains the authority for order state.

## Operator experience

A single pending-order reply that matches the expected format receives two
Telegram inline buttons:

- **주문 확인** submits the order's displayed 10-digit public order number and
  phone to the existing DEV operator bridge. The existing stock check, order
  state transition, and duplicate/update protections remain in effect.
- **주문 상세** opens the existing read-only detail response, scoped to that
  same order and phone.

No buttons are attached to unrelated text, order lists, completed orders, or
messages whose order identifier does not match the callback.

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
