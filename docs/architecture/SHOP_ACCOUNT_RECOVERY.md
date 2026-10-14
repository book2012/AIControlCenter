# Agachichi account recovery — API design and delivery gate

## Decision and current state

Recovery is an AIControlCenter-owned workflow. WooCommerce remains the credential
and customer-profile store, exposed through a narrowly scoped adapter. The account
plugin may render and submit forms, but it must not decide identity matches,
issue reset credentials, or send messages.

Twilio is selected for account recovery. Use Twilio Verify for the ID-recovery
OTP and Twilio Programmable Messaging with a dedicated Messaging Service for
password-reset links. The existing DEV config has Verify enabled for exactly one
configured test phone but has no Messaging Service SID or sender. A DEV-only
Messaging adapter exists; it rejects every recipient except that configured
test phone. The recovery service, same-origin FastAPI router, fixed-test-phone DEV Verify
adapter, Core Woo adapter, and DEV-only WordPress recovery bridge are implemented
with mocked-provider tests. None is wired into a runtime. No
SMS has been sent. The adapter uses
Twilio's Messages resource with `To`, `MessagingServiceSid`, and `Body`, then
binds status reconciliation to the returned Message SID, test recipient, and
Messaging Service. See the
[Twilio Messages resource](https://www.twilio.com/docs/messaging/api/message-resource).

## Customer flows

### Find login ID

1. Ask for the registered name and mobile number.
2. Send a short-lived one-time code to that number only through an approved,
   recovery-scoped provider adapter.
3. On valid code, resolve the exact WooCommerce account through the AIControlCenter
   identity adapter. Do not match browser-supplied user IDs or Telegram identity.
4. Return the full login ID only after successful phone verification, as
   requested. Never include it in logs, analytics, or an unverified response.
5. Invalid, missing, duplicate, throttled, and provider-unknown cases use the same
   public response and do not reveal whether an account exists.

### Reset password

1. Ask for login ID, registered name, and mobile number.
2. Always return the same generic acknowledgement, whether the tuple matches or
   not. Apply IP, account-reference, phone-binding, and global rate limits.
3. For one exact match, create a cryptographically random, short-lived,
   single-use reset secret. Persist only its keyed digest, bind it to the matched
   customer and purpose, and send a reset URL through the approved provider.
4. The reset page accepts the secret once, validates expiry and purpose, then
   forwards a password update through the narrowly scoped WooCommerce credential
   adapter. Consume the secret and audit the outcome atomically where the store
   permits it; otherwise use explicit pending/unknown-outcome reconciliation.
5. A resend is a new, explicitly requested workflow only after reconciliation;
   network timeout never triggers automatic resend.

## API contract to implement

Public operations should be versioned and return no-store JSON:

- `POST /v1/shop/account-recovery/id-challenge`
  - Request: registered name and mobile.
  - Response: generic challenge acknowledgement and opaque challenge reference.
- `POST /v1/shop/account-recovery/id-confirm`
  - Request: challenge reference and one-time code.
  - Response: full verified account ID, or generic
    failure.
- `POST /v1/shop/account-recovery/password-reset`
  - Request: login ID, registered name, mobile.
  - Response: generic acknowledgement independent of account match or SMS outcome.
- `POST /v1/shop/account-recovery/password-reset/complete`
  - Request: reset secret and new password.
  - Response: generic completion/failure; secret is one-time and expires quickly.

The API must enforce CSRF/origin protections appropriate to the storefront,
request size limits, strict input validation, per-IP and per-identity throttles,
idempotency for provider dispatch, and no-store/no-referrer handling for reset
pages. Public responses, metrics, and audit records must not contain raw phone,
OTP, reset secret, password, or message content. Audit records may include opaque
account/resource refs, action, outcome, correlation ID, and timestamp.

## Required ports and states

AIControlCenter owns the recovery policy/service, rate limiting, token lifecycle,
audit, and reconciliation. Adapters are limited to:

- exact customer lookup by normalized login ID/name/verified phone binding;
- phone challenge / recovery-link delivery with a provider receipt and status
  lookup bound to the exact recipient and idempotency key;
- password credential update in WooCommerce, with a definitive receipt or an
  explicit unknown outcome.

Provider dispatch states: `CLAIMED`, `ACCEPTED`, `FAILED`, `UNKNOWN_OUTCOME`,
`RECONCILED_DELIVERED`, `RECONCILED_FAILED`. Never treat HTTP acceptance as
handset delivery and never automatically retry `UNKNOWN_OUTCOME`.

## Implementation status

Implemented but not runtime-enabled: the AIControlCenter recovery service,
SQLite claims/tokens/rate buckets/audit records, same-origin API router, fixed
DEV Verify adapter, Woo account adapter, and narrow WordPress bridge. The API
module is deliberately not registered in the shared production app or DEV order
runtime. The dedicated WordPress recovery role and Application Password have not
been provisioned. Runtime binding, functional UI, and live SMS validation are
absent.

Validation: 74 targeted tests passed across recovery service/API, Twilio Verify
and Messaging adapters, Woo account adapter, DEV guest phone verification, and
production customer isolation. The WordPress bridge passed PHP syntax lint in
the DEV WordPress container; it was not installed or activated. API tests use
fake providers; no Twilio request or SMS occurred.

## WooCommerce adapter boundary

The WordPress bridge is a separate account-recovery plugin. It exposes only
exact-match ID lookup, exact-match reset lookup, post-OTP phone re-resolution,
and password update. Every route requires HTTPS Basic authentication via a
dedicated WordPress Application Password, the aicc_recovery_service role, and
the aicc_manage_account_recovery capability. The Core adapter pins the DEV HTTPS
origin, disables environment proxies and redirects, bounds response bodies, and
validates every returned account reference and identity field. Woo REST keys,
admin credentials, and public storefront requests are not accepted.

No recovery role, service user, Application Password, plugin activation, or
runtime composition has been provisioned. The bridge PHP syntax was checked
read-only in the DEV WordPress container.

## Enablement gates

Do not expose functional recovery forms until all gates pass:

1. Provision a dedicated Twilio Messaging Service, attach an eligible sender,
   and add its SID to the private DEV recovery config; keep order-notification
   configuration independent.
2. Bind the new DEV Verify adapter to the recovery service using the existing
   fixed-test-phone composition without broadening recipient scope.
3. Privately provision the dedicated DEV recovery role and WordPress
   Application Password. Never reuse Woo REST or administrator keys.
4. Bind the Core Woo adapter to the DEV bridge and verify exact identity lookup
   with synthetic customer data.
5. Add a durable single-attempt claim/outbox around message dispatch, persist the
   Twilio Message SID, and reconcile delivery without automatic resend.
6. After provider setup and test-plan review, separately authorize one DEV
   handset test to the configured test phone; no other recipient.
7. Add UI and regressions for throttling, enumeration resistance, concurrency,
   expiry, replay, audit redaction, and provider-unknown outcomes.
8. Mount in isolated DEV only and verify ID/reset journeys with synthetic
   accounts. No real customer account mutation and no PROD activation.

Adapter tests: `tests/test_shop_twilio_recovery_messaging.py` (9 passed). These
use a mocked transport; they do not contact Twilio or send SMS.

Adapter tests:
tests/test_shop_woocommerce_account_recovery.py (11 tests) use a fake HTTP
session. No live WordPress user, password, or network API was exercised.

## Deferred UI

After the gates, add “아이디 찾기” and “비밀번호 재설정” links to the existing
agachichi login page. Reuse the account page header/theme. ID lookup should show
the result only after phone verification. Password request UI must show the same
acknowledgement for matching and non-matching details. The reset page must never
put the secret in analytics, referrer headers, browser logs, or persistent local
storage.

## Telegram remains a separate milestone

The customer Shopping/Sales Bot remains separate from the operator bot. Guests
stay unlinked; a member binding requires an authenticated account-link challenge.
First-purchase classification is based on no previous successful paid order.
This work does not change operator-bot credentials or order routing. See
[Telegram customer bot architecture](SHOP_TELEGRAM_CUSTOMER_BOT.md).
