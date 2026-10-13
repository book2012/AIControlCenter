# Telegram customer identity and first-purchase routing

## Scope
This is a separate customer-facing Shopping/Sales Bot. The existing papachichi
DEV bot is an operator interface with a fixed operator chat and user allowlist;
it must not accept customer messages or customer identity claims. The
mommychichi PROD operator bot remains isolated.

## Customer classification
- Unlinked Telegram conversations are guests. They may browse and ask product
  questions, but the bot must not infer a store account from a Telegram name,
  username, or phone text.
- A member is recognized only after an explicit, short-lived account-link
  challenge completed while authenticated to the agachichi account (or an
  equivalent verified-phone flow). Bind Telegram's stable numeric user ID to
  the WooCommerce customer through AIControlCenter, with revocation and audit.
- Once linked, classify the member as a first-purchase customer when there is no
  prior successful paid order; otherwise classify as a returning purchaser.
  Pending, failed, and cancelled orders do not count. Re-evaluate before order
  submission to avoid stale classification.
- Keep the member/guest and first-purchase labels internal to routing; never
  disclose another customer's account or order information in group chats.
- The Telegram bot remains an adapter. AIControlCenter owns identity linking,
  customer/order lookup, classification, authorization, and audit.

## Runtime status
No customer-facing Shopping/Sales Bot or Telegram-to-customer binding is
currently composed. Telegram code in the order service is a fixed-recipient
operator flow. Implementing this requirement needs a separately scoped bot
credential, isolated cursor/conversation store, account-link route, Woo order
history adapter, and tests for guest/member, first purchase/repeat purchase,
revocation, and duplicate updates. Do not alter the operator bot as a shortcut.
