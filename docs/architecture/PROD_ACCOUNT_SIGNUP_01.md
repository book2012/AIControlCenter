# PROD customer signup architecture 01

## Decision and current state

Customer signup is intentionally disabled on PROD today. The PROD login page
uses WooCommerce authentication, and `/my-account/register/` remains blocked.
This proposal adds an explicit, separately gated customer-registration capability
for `agachichi.duckdns.org`; it does not enable the feature or change live
WordPress, WooCommerce, provider, customer, order, inventory, or DNS state.

DEV remains a test environment. Its synthetic identities, fixed test-phone
verification, keys, provider configuration, database, WordPress bridge and
WooCommerce store must never be reused by PROD.

## Ownership and boundaries

- **AIControlCenter Core** owns registration policy and orchestration: challenge
  lifecycle, verification, uniqueness checks, throttling, idempotency, audit,
  outcome reconciliation and feature gating.
- **WooCommerce** remains the source of truth for customer credentials and
  account profile. A narrow production adapter creates a `customer` only after
  Core authorizes it and reads the created record back.
- **WordPress** serves the host-gated form and same-origin transport. Its
  presentation plugin does not decide identity matches, verify OTPs, create
  credentials, or send messages.
- **Infrastructure** keeps production secrets and persistent state on the Mac
  mini Control Plane. No customer-account business logic or state is moved to
  the Ubuntu worker.
- **Commerce stays separate**: registration creates no order, cart, reservation,
  stock change, payment, or order notification. Signup is not checkout.
- **Product operator registration** is unrelated; it continues through the
  separate guarded PROD product registrar.

Keep WooCommerce's native public registration disabled. Do not enable a global
Woo setting or public WordPress route that bypasses Core verification. The
custom form and private bridge are the only planned registration path.

## Proposed customer experience

The existing login screen gains a “회원가입” link only when the PROD feature
flag and all readiness gates are satisfied. It opens a mobile-friendly,
Agachichi-branded registration form. The current screen remains login-only while
the flag is off.

Collect the minimum account information needed for the agreed store policy:
login ID (reuse the DEV 4–20 ASCII character rule), email, password and
confirmation, legal name, and Korean mobile number. Nickname is optional.
Home/shipping address is collected at checkout or account address editing, not
required for signup. Confirm the privacy notice and terms before submission.
Email must be verified before activation; phone OTP is also required for the
initial production policy. The production messaging and email-verification
providers are separate replaceable adapters. No provider is currently asserted
as provisioned for production.

A collision on login ID, email, or normalized phone must not disclose which
identity already exists. Return a uniform response and direct the user to the
existing login/recovery flow. Never merge accounts automatically.

## Registration flow

1. The browser loads a same-origin, no-store form from the PROD account plugin.
   CSRF/origin checks and request-size limits apply to every mutation request.
2. The user requests a phone challenge. Core normalizes the number and applies
   per-IP, per-number, per-session and global throttles before dispatch.
3. A production OTP adapter sends a short-lived one-time code. Provider timeout
   is recorded as `UNKNOWN_OUTCOME`; it is not automatically resent.
4. The user confirms the code. Core validates the exact challenge and attempt
   budget, then issues a short-lived, single-use registration ticket bound to
   the session, phone, purpose, expiry and random nonce. Store only a keyed
   digest of the ticket/OTP material.
5. Email verification is completed through a separate expiring, single-use
   token. Do not activate an account until both required contacts are verified.
6. The final registration request carries the ticket, email token, validated
   profile and password. Core rechecks uniqueness, ticket consumption, terms
   version, throttles and idempotency before creating a durable operation claim.
7. A private, narrowly scoped WordPress bridge creates only a WooCommerce
   `customer` with the verified phone and approved profile fields. Password
   passes transiently over HTTPS/private service authentication to WooCommerce;
   AIControlCenter must not persist or log it.
8. The adapter reads the exact created customer back and validates role and
   identity bindings. Only a definitive readback marks the account active.
   Ambiguous write outcomes enter reconciliation; retry is blocked until the
   exact operation is resolved.
9. Show a generic completion result and redirect to the canonical login page.
   Native WooCommerce login remains the credential/session owner. No automatic
   login is required for the initial release.

Suggested Core endpoints (not implemented):

- `POST /v1/shop/account-registration/phone-challenge`
- `POST /v1/shop/account-registration/phone-confirm`
- `POST /v1/shop/account-registration/email-challenge`
- `POST /v1/shop/account-registration/email-confirm`
- `POST /v1/shop/account-registration/complete`

All public responses use no-store headers and avoid account-existence signals.
Keep secrets out of referrers, browser storage, URLs where practical, analytics,
metrics and logs.

## Security, privacy and reliability

- Initial tunable defaults: OTP expires in 5 minutes; at most 5 confirmation
  attempts per challenge; resend cooldown 60 seconds; per-number limit 5/day;
  per-IP limit 10/hour. Add a conservative global circuit breaker and alert.
  Reassess against observed abuse before increasing limits.
- Bind every challenge and operation to purpose, environment, origin/session,
  normalized identity and an unpredictable nonce. Reject replay and cross-env
  tokens. Signatures/keys are environment-specific and have independent
  rotation procedures.
- Production and DEV have distinct databases, WooCommerce origins, bridge
  identities, application passwords, OTP/email credentials, signing keys,
  rate-limit state and audit stores. No credential or identity copying.
- The bridge uses a dedicated service role/capability that can create/read only
  customers for this operation. Never use administrator credentials, Woo REST
  keys, or public `wp-json`/admin-ajax endpoints.
- Use uniform external responses for duplicate and missing identities. Keep
  audit references opaque or keyed-pseudonymous; do not log raw email, phone,
  password, OTP, tickets, reset tokens, or message bodies.
- Persist explicit states such as `CLAIMED`, `PENDING_VERIFICATION`,
  `CREATE_ACCEPTED`, `CREATE_FAILED`, `UNKNOWN_OUTCOME`, `ACTIVE`, and
  `RECONCILED`. Enforce one-time idempotency and reconciliation before any
  retry after an ambiguous provider or WooCommerce result.
- Define retention, deletion, consent text and customer privacy disclosures
  before launch. Keep this design separate from a legal-compliance claim.

## DEV/PROD matrix

| Concern | DEV | PROD |
| --- | --- | --- |
| Purpose | Feature tests and synthetic journeys | Real customer accounts after launch gate |
| Phone | Existing fixed test phone/fake provider only | Dedicated production OTP service and approved sender |
| Email | Fake/local test adapter | Separately provisioned verified-email provider |
| WooCommerce | Isolated DEV store and synthetic users | PROD store through dedicated least-privilege bridge |
| Secrets/state | DEV-only and disposable where possible | Separate protected credentials, durable claims and audit |
| Public signup | Test-only UI/route when explicitly enabled | Disabled by default; host-gated dedicated rollout flag |
| Orders/payments/stock | Unchanged by signup tests | Unchanged by account creation |

DEV tests must not send to arbitrary phones or contact PROD services. PROD dry
runs use fake adapters and do not create a real customer. Live provider delivery
or production test-account creation requires its own reviewed, explicit
authorization.

## Delivery gates

1. Implement Core registration service, durable claims, idempotency,
   enumeration-resistant responses, audit redaction and reconciliation tests.
2. Implement separate production phone/email provider ports and test fakes.
   Confirm provider, sender, delivery policy, budgets and secret custody before
   loading production credentials.
3. Implement a separate PROD WordPress bridge role and application password;
   prove it cannot edit/delete customers, change roles, access orders or manage
   products.
4. Add isolated DEV coverage for duplicate identities, expiry, replay,
   throttling, concurrency, account creation readback and unknown outcomes.
   Keep DEV fixed-number restrictions intact.
5. Run PROD composition dry-run with fake adapters; verify host allowlist,
   ingress, flag defaults, logs/metrics redaction and rollback.
6. Review privacy/terms copy, support recovery behavior, retention and
   operational ownership.
7. Enable PROD signup only after all gates pass and a separately authorized
   rollout. Keep signup, checkout, payment, order SMS and product publishing as
   independent flags.

## Out of scope and unresolved decisions

- No implementation, provider provisioning, SMS/email dispatch, real customer
  creation, signup activation, checkout or PROD deployment in this design task.
- No migration or synchronization of DEV accounts into PROD.
- Recovery remains governed by
  [account recovery design](SHOP_ACCOUNT_RECOVERY.md); registration must use
  compatible verified identity bindings but does not activate recovery.
- Confirm the preferred login ID policy (custom username as DEV parity versus
  email-first UX), final consent/terms wording, retention periods and approved
  production messaging/email providers during implementation planning.

## Related documents

- [PROD account presentation](PROD_ACCOUNT_PRESENTATION_01.md)
- [DEV/PROD release boundaries](SHOP_DEV_PROD_RELEASE_BOUNDARIES.md)
- [Account recovery](SHOP_ACCOUNT_RECOVERY.md)
- [DEV registration flow](../homepage/DEV-ACCOUNT-REGISTRATION-01.md)
