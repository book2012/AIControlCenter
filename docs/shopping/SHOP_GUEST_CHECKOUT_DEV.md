# DEV guest checkout, Telegram and local inquiry AI

## Active customer experience
At https://dev.bokstory.duckdns.org/dev-order the customer creates no username/password. Ask about the product, select an option, add to cart or choose single-item ordering, prove phone possession, enter recipient/postcode/address, review the authoritative amount and delivery details, then explicitly confirm. The verified number supplies the contact; caller-supplied contact/identity/price/authority fields are not accepted.

This release supports the isolated mapped blouse, S/M variations and the configured DEV phone. Existing DEV edge Basic Auth remains. The original demonstration storefront and the full 120-product catalog have not been migrated or integrated with this separate chat entry. Phone verification does not automatically create an order.

## Architecture and write authority
Mac AIControlCenter owns guest identity, session, checkout authority, immutable private delivery draft, durable provider dispatch and Telegram operator review. WooCommerce owns product/variant price and stock and stores the pending unpaid order and delivery details. Independently allocated internal customer/contact references are maintained privately; an isolated internal Woo customer record is provisioned idempotently without requiring customer credentials in the shopping experience. This single-phone mapping is not a production multi-customer identity repository.

A private 0600 SQLite checkout database binds the immutable cart, quote and delivery snapshot to the authenticated customer, issuing session and server operation key. PREPARED is not CONFIRMED: explicit checkout confirmation changes this gate before the existing Core writer can dispatch. A direct guest call to the ordinary order-create path without that gate is denied. Private snapshots bind delivery, contact, line items and authoritative quote using a digest; they are not added to the public ledger or Telegram payload.

Before confirmation and again before provider dispatch, actual variation price, published/in-stock status, managed stock quantity and no-backorder policy are checked. DEV explicitly uses KRW, no tax and zero shipping; production shipping/tax policy is not inherited. Provider replies must match customer, private billing/shipping, delivery digest, final amount, zero tax/shipping and the original operation metadata. Explicit reconciliation also verifies the private snapshot. Response loss/mismatch keeps the existing operation uncertain; no automatic new key, provider POST or Telegram resend occurs.

The existing order ledger/outbox atomically completes the order and queues Telegram notification. Operator confirmation changes local review only, never payment, fulfillment or WooCommerce status. Customer operation lookup remains bound to the issuing session; phone reauthentication historical lookup is a separate future contract.

## Local AI inquiry
Ollama runs on Mac loopback 127.0.0.1:11434. Qwen3:4b was installed because the original model inventory was empty; its current digest is recorded in validation JSON. An explicit bounded adapter sends product context and a question only to this endpoint, with one inference at a time, finite timeout, structured output, no tools, no proxy/redirect/cloud fallback. No customer session, OTP or private delivery record is sent to the model.

The local model judges STOCK, PRICE, DESCRIPTION, PURCHASE or OPERATOR. Core renders registered WooCommerce facts; model text cannot invent a price, promise delivery, authenticate a customer or submit an order. Invalid/unavailable AI responses ask for operator review. This is a bounded grounded shopping assistant, not unrestricted free-form policy generation. Live paraphrased size, price and unsupported delivery-promise judgments were checked.

References: https://ollama.com/library/qwen3:4b and https://docs.ollama.com/api/chat .

## Validation and actual DEV evidence
- 700 selected Python regression tests passed, 20 existing deprecation warnings.
- Isolated real Chrome exercised inquiry/cart, inert phone verification, customer session, delivery review, double-click confirmation, fake Telegram operator review and customer status. Exactly one fake writer call and two fake Telegram messages; no external provider requests in that harness.
- Separately, the actual phone-verified private session created isolated WooCommerce order #15 for KRW 29,000 using clearly synthetic DEV delivery information. The pending unpaid provider reply matched that private delivery snapshot and amount.
- Exact replay returned HTTP 200 without another create. Real Telegram ORDER_CREATED message #9 and OPERATOR_CONFIRMED message #11 were SENT. Actual human review is CONFIRMED; customer operation status returned HTTP 200 / COMPLETED / CONFIRMED.
- Existing order #14 and its review/notifications were preserved. No production mutation or payment/fulfillment occurred. Public authenticated browser end-to-end live-provider testing remains a human acceptance task; the automated browser and actual-provider checks are separate evidence.

## Operations and remaining production gates
Private configuration/state and SQLite backups remain outside Git. The one-shot guest live probe refuses a second confirm attempt; inspect saved state instead. The guest provider customer provisioner targets only the checked aicc-order-dev WordPress/database project. No customer database, synthetic order, credential or DEV shipping policy is a production migration input.

Current API/facade are still owned DEV processes rather than installed launchd jobs. A reviewed persistent edge deployment, service supervision/restart rehearsal, complete approved product/photo mapping, production identity/shipping policy, appropriate private-data retention/protection and production backup/rollback proof remain required before activation. Prepared draft expiry or quote changes conservatively block confirmation; uncertain operations require inspection rather than a new order.
