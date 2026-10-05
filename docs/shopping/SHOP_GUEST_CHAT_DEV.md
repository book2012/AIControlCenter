# Guest chat shopping — DEV foundation

## Customer flow and architecture
The customer creates no username or password. Anonymous product inquiry uses current WooCommerce catalog information; stock/options/price/description are supported, unknown questions require operator review. A purchase phrase opens the order workflow but never constitutes an order submission. Single-item and cart checkout share the quote and future verification flow.

Target: guest inquiry → item/options/cart → phone ownership verification → recipient and shipping address → authoritative final review → explicit customer confirmation → durable order operation → Telegram operator review → customer status. AIControlCenter remains the sole authority; WooCommerce owns commerce facts, Telegram carries operator notifications. Phone ownership must be proven by the approved phone-verification service before internal customer/session issuance. The current synthetic test-account fixture must never authenticate a guest.

## Implemented and active in isolated DEV
- Entry https://dev.bokstory.duckdns.org/dev-order redirects to the blouse chat.
- No customer account is required for inquiry or quote. Existing DEV edge Basic Auth still protects the environment.
- Product-context inquiry is a deterministic grounded assistant, not a general LLM. It does not invent delivery promises or policy.
- Cart stores only product IDs, variation IDs and quantities in sessionStorage; no phone, address, session credential or OTP.
- Quotes validate real catalog source, active stock flags, required and available variation, duplicate lines and bounded quantities. Client prices/identity/authentication fields are rejected.
- Quote totals are provisional item totals; shipping fee, final amount and quantity availability must be revalidated at confirmation. Current Product contract exposes stock flags rather than authoritative purchasable quantities or per-variation prices.
- SMS verification, delivery capture and final confirmation are explicitly disabled and shown as unavailable. No guest order is created, even if an older synthetic test-account cookie exists.
- Supported product set is the one isolated mapped blouse; multiple product lines are supported and tested using an inert multi-product catalog, but the full 120-product catalog remains unmapped.
- Original demonstration storefront is unchanged; general product-page/cart integration remains a subsequent release. The separate guest chat path is available now.

## Validation
674 Python tests passed, with 20 existing deprecation warnings. Twelve new guest tests cover grounding, catalog source, anonymous routes, unavailable options, duplicates, forged authority/prices, bounded payloads, origin and safe HTML. Isolated real Chrome exercised guest inquiry, add-to-cart, quote and disabled unverified confirmation; zero provider writes and zero external provider requests.
Live isolated DEV returned 200 for anonymous stock inquiry and quote; S/M available, L unavailable, item total KRW 29,000. Previously confirmed order #14 and Telegram messages #6/#8 were preserved. No SMS was sent and no production mutation was performed.

## Twilio setup required
The user selected an existing Twilio account. Locally fill `/Users/kyouhan/.config/aicontrolcenter-dev-order/phone-verification.private.json` (0600): credentials.account_sid, credentials.auth_token, credentials.verify_service_sid, and test_phone in E.164 format. The template remains enabled=false and is not loaded into the current guest runtime. Do not paste secrets into chat or commit them.
Official reference: https://www.twilio.com/docs/verify/api/verification and https://www.twilio.com/docs/verify/api/service-rate-limits .

## Remaining implementation and release gates
Install governed Twilio Verify start/check transport using existing provider-neutral phone verification and destination-resolution boundaries, durable dispatch ownership, bounded attempt/rate limits and no automatic resend after uncertain outcomes. Scope DEV sends to the explicitly configured test phone. A valid provider response must remain bound to the browser challenge and normalized phone identity; neither a boolean from the browser nor a synthetic receipt is proof.

Then issue a guest customer session from validated evidence, collect recipient/address behind that session with origin/CSRF checks, establish a private shipping snapshot bound to the exact order intent/digest and final amount, and add an explicit confirmation operation. Do not mutate the immutable existing order command or add plaintext PII to notification/ledger payloads casually. Provider guest identity mapping and delivery payload governance require their own reviewed contracts before enabling writes. Phone number is the verified contact; third-party delivery contacts need explicit supported policy.

Finally integrate the demonstration storefront's buttons/cart, migrate approved product/variation/photo mappings, install supervised Mac services and persistent DEV edge deployment, and validate production-specific fresh state, backup/rollback and deployment package. Production remains inactive.
