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

## Step 2 proposal — providers, consent and retention

### Provider selection

Recommended production path:

- Use **Twilio Verify SMS** for phone OTP, consistent with the already selected
  account-recovery vendor. Use a 4-digit code and the exact user-approved copy:
  `[Agachichi] 인증번호 {{code}} 입니다`. Create a signup-specific PROD Verify
  Service SID and restricted API credentials. Do not reuse the DEV test-number
  configuration or recovery service identity. Recovery-link Messaging remains
  a distinct workflow.
- Use **Twilio Verify email verification through Twilio SendGrid** for email
  OTP. Twilio documents this integration as requiring a SendGrid account, a
  restricted Mail Send API key, a verification template, and authenticated
  sending domain. When `agachichi.com` is owned and DNS can be controlled,
  authenticate a dedicated sender subdomain before sending.
- Keep both as replaceable Core ports. Send only the destination and
  verification content to the providers; do not send customer names, login IDs,
  addresses, or passwords.
- Twilio requires an approved pre-approved/custom Verify template for customized
  SMS copy; custom templates are handled case-by-case. Do not use the deprecated
  `CustomMessage` override. Request/verify the Korean template and 4-digit
  substitution before any live send.
- This is a provider recommendation, not provisioning authorization. Production
  service SIDs, keys, DNS records, templates, and live sends remain absent.

Twilio Verify supports email as a verification channel and its email setup uses
Twilio SendGrid. The provider integration and domain authentication are described
in the [Verify service API](https://www.twilio.com/docs/verify/api/service),
[Verify email setup](https://www.twilio.com/docs/verify/email), and
[SendGrid email authentication](https://www.twilio.com/docs/sendgrid/concepts/security/email-authentication).

### Draft consent presentation

Keep terms, essential personal-information processing, and any required
international transfer disclosure distinguishable. Do not include marketing
consent in signup; if added later, it must be optional and unchecked.

Proposed form labels (final wording and lawful basis require privacy review):

- `[필수] Agachichi 이용약관에 동의합니다.`
- `[필수] 회원가입 및 계정 관리를 위한 개인정보 수집·이용 내용을 확인했습니다.`
  Show an adjacent disclosure listing login ID, email, name and mobile number;
  account creation, contact verification and account management purposes; and
  retention until withdrawal, subject to a separately stated statutory
  retention requirement where applicable.
- Where a consent basis is used for overseas transfer, show a separate
  disclosure/choice before the first provider call. It must identify the
  actual recipient legal entity, destination country, transfer method and
  timing, data items, purpose, retention period, refusal option and effect.
  Confirm these facts from the provider contract and account region before
  publishing; do not assume the country from the vendor brand.

The Privacy Act requires collection to be limited to the minimum necessary and
requires overseas-transfer conditions and disclosures to be checked. Twilio and
SendGrid processing of Korean contact data is therefore a launch gate, not
something implied by ordinary terms acceptance. See the official
[Personal Information Protection Act, Articles 16 and 28-8](https://www.law.go.kr/LSW/lsInfoP.do?ancYnChk=0&lsId=011357)
and [Article 21](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029335387).

### Retention proposal

- OTP values and passwords are never written to Core storage or logs.
- Keep registration challenge state only as keyed destination digests, opaque
  provider references, lifecycle and timestamps. Challenge lifetime: 5 minutes;
  one-use registration ticket lifetime: 5 minutes. Delete or irreversibly
  expire those records after completion/expiry; retain a non-PII replay tombstone
  only until the original ticket could no longer be accepted.
- Keep rate-limit buckets as keyed digests only, for the configured window
  (initially 24 hours), then purge them. Do not store raw IP or contact values
  in signup audit.
- Do not persist an unfinished profile in Core. Hold submitted fields only for
  the active request; WooCommerce stores the verified profile after successful
  creation.
- Keep the active account profile until account withdrawal. At withdrawal,
  remove account-only fields unless a specific legal retention duty applies;
  isolate any transaction records subject to retention rather than retaining
  the whole customer account. Record the accepted terms/notice version and
  timestamp with the account; retention after withdrawal must be covered by the
  approved privacy schedule.
- Obtain provider deletion/retention terms for verification metadata and
  document the applicable cross-border processing arrangement before launch.
  No fixed post-withdrawal period is asserted until the business/legal review
  determines which records must be preserved.

### Decision status

The user approved the SMS copy `[Agachichi] 인증번호 ×××× 입니다`; the design
interprets the mask as a four-digit code and maps the provider template to
`[Agachichi] 인증번호 {{code}} 입니다`. A side-effect-free preview formatter
and tests are implemented in `core/shopping/adapters/signup_verification_message.py`.
Twilio Verify + SendGrid is the recommended provider path, and the retention
rules above are the proposed technical defaults. Provider-account/legal-entity
details, transfer basis/disclosure, final Korean consent wording, and the
post-withdrawal schedule remain launch blockers. No provider has been configured
or contacted.

## First implementation slice — input contract

Implemented as an isolated, side-effect-free Core module in
`core/shopping/account_registration.py`. It validates the DEV-compatible
4–20-character ASCII login ID, email, password and confirmation, legal name,
Korean mobile format, explicit terms/privacy consent, and terms version. It
returns a redacted candidate object only; the result does not prove phone/email
ownership and cannot authorize persistence or WooCommerce account creation.

Focused tests: `tests/test_shop_account_registration_input.py` plus the existing
account-recovery regression suite (26 passed). The SMS copy/preview contract is
covered by `tests/test_shop_signup_verification_message.py`; the combined
focused suite now has 33 passing tests. No API/router/runtime composition,
provider, database schema, WordPress bridge, WooCommerce call, PROD flag, or
production state was changed.

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

- No signup API/runtime composition, uniqueness checks, complete registration
  operation, live provider provisioning, SMS/email dispatch, customer creation,
  signup activation, checkout or PROD deployment. Current Core verification
  and two-contact claim foundations remain unmounted and fake-only.
- No migration or synchronization of DEV accounts into PROD.
- Recovery remains governed by
  [account recovery design](SHOP_ACCOUNT_RECOVERY.md); registration must use
  compatible verified identity bindings but does not activate recovery.
- Login ID policy is set to the DEV-compatible custom username (4–20 ASCII
  characters); confirm final consent/terms wording, retention periods and
  approved production messaging/email providers during implementation planning.

## Related documents

- [PROD account presentation](PROD_ACCOUNT_PRESENTATION_01.md)
- [DEV/PROD release boundaries](SHOP_DEV_PROD_RELEASE_BOUNDARIES.md)
- [Account recovery](SHOP_ACCOUNT_RECOVERY.md)
- [DEV registration flow](../homepage/DEV-ACCOUNT-REGISTRATION-01.md)


## Implementation slice — fake-only phone verification core

Implemented as an isolated Core service in `core/shopping/signup_verification.py`. Its provider is injected through a narrow port; the included tests use an in-memory fake and perform no network calls. The service issues five-minute phone challenges and phone-verification tickets, enforces a 60-second resend cooldown, five starts per phone per day, ten per client per hour, and five code attempts. It stores keyed digests and opaque provider references in an explicitly initialized, owner-only SQLite store. Construction is inert; it does not initialize the database, bind an API/runtime, create an account, or call WooCommerce. Ambiguous provider outcomes are quarantined without an automatic retry.

The phone ticket proves phone verification only. Email verification and the two-contact claim are now implemented as fake-only Core foundations, followed by a privacy-preserving uniqueness preflight and durable one-attempt registration operation/reconciliation boundary. These components are not mounted in an API/runtime. Production adapters, audit integration, WordPress bridge and WooCommerce customer creation remain unimplemented. Production signup remains disabled; no production configuration, SMS provider, customer, or runtime state was touched.

Initial phone-only validation: 50 tests passed. Current combined signup, operation, message, input and recovery suite: 66 passed. All external-facing tests use in-memory fakes with no network I/O.

## Delivery gates


## Implementation slice — fake-only email and two-contact claim

Added `core/shopping/signup_email_and_claim.py` on top of the isolated phone-verification store. Email challenges and tickets are session-bound, expire after five minutes, enforce attempt/resend limits and a shared phone/email client budget, and use an injected provider port. The final claim operation revalidates the registration candidate and required terms/privacy consent, checks that both proof tickets match the candidate phone/email and same session, then consumes both tickets and records an idempotent durable claim in one SQLite transaction. Only keyed digests, ticket references, session binding, idempotency and terms-version evidence persist; password, name, login ID and contact values are not stored.

The claim is a Core proof/operation boundary only. It does not check account uniqueness, create an account, invoke WooCommerce, or act as runtime/API authorization. Email provider delivery/template and consent wording remain unconfigured; there is no live provider. At that implementation checkpoint, the combined focused suite had 58 passing tests.

## Implementation slice — uniqueness and durable registration operation

Added `core/shopping/signup_registration_operation.py`. A read-only injected port checks login ID, email and phone on every request; the public-facing result does not identify which field matched. If lookup fails, the claim remains unmodified and no write begins. For a clear candidate, the service durably records `DISPATCHING` before invoking the customer-write port, then requires exact identity and role readback before `ACTIVE`. The production adapter must still enforce uniqueness at write time to close the preflight race. Ambiguous writes become `UNKNOWN_OUTCOME`; the same claim cannot dispatch again. Reconciliation is read-only and resolves only a found customer with matching identity or a definitive absence.

Tests use a memory-only fake customer port. No production adapter, API/runtime route, WordPress bridge, WooCommerce call, real customer, or PROD mutation exists. The future PROD adapter must enforce least privilege and verify the created WooCommerce role and identity bindings; DEV composition still requires an explicit environment boundary. Current combined focused suite: 66 passed.

## Implementation slice — synthetic DEV HTTP composition

Added core/shopping/signup_dev_app.py as an unmounted test-only FastAPI factory. It requires explicit environment=DEV, an explicit feature flag, all services to share one store under a DEV data root, and providers/customer port marked as DEV test doubles. Requests require the exact DEV origin and host and a loopback peer; session binding uses an HttpOnly, Secure, SameSite=Strict cookie. Request bodies are bounded, responses are no-store, and public signup completion maps internal non-success outcomes to one generic response.

Synthetic TestClient E2E exercised phone/email challenges, same-session proofs, consent validation, durable claim, read-only uniqueness checks, one fake customer write and matching readback. Negative tests reject PROD environment, disabled signup, data-root escape, unmarked provider and wrong origin/host. The factory is not imported by core/api/app and does not connect to the running DEV or PROD service. Combined focused suite: 69 passed with one Starlette/httpx deprecation warning.

This is pre-PROD readiness evidence only. It does not prove real ingress, persistent DEV deployment, WooCommerce least-privilege behavior, production template delivery, privacy/legal readiness or operational recovery. Do not connect PROD before those separate checks.
