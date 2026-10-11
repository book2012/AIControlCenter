# SOLAPI order and shipping SMS — DEV preparation

2026-10-12. User resumed order-notification SMS. Phone OTP migration and PROD notification activation are outside this checkpoint.

## Current external blocker

One explicitly authorized connectivity SMS was sent to the existing private DEV test recipient. Authentication and submission succeeded; bound read-only message-status lookup returned FAILED / 3113 (sender number subscribed to number-spoofing SMS blocking). The private journal is solapi-order-test-20261012.private.json, 0600, never committed. No automatic resend or enabled flag change occurred. The sender's carrier service must be disabled or another SOLAPI-registered eligible sender provided before the next real delivery test.

## Provider and outbox

Pinned api.solapi.com, HMAC-SHA256 with per-request date/salt, disabled proxy inheritance/redirects and one POST attempt. Domestic +82 phone input becomes 010 digits with country 82. EUC-KR byte validation chooses SMS through 90 bytes, LMS through 2000 bytes. Long orders use a bounded summary plus the authenticated customer lookup link, preserving amount/account guidance. Missing/invalid content is detected before claiming.

Receipt binds group, message, recipient, sender, original-text digest and custom event digest. Accepted submission is not delivery. Read-only status polling binds the same receipt; final code 4000 becomes DELIVERED, rejection/failure becomes FAILED, unresolved delivery remains ACCEPTED. Neither failure nor ambiguity permits another POST. Local provider receipts and final states are persisted privately; status polls are spaced 30 seconds.

Existing DEV order/SMS outbox is composed with optional SOLAPI config while retaining existing Twilio configuration. Bank details stay in the existing private order-notification file. SOLAPI enabled and per-purpose order_confirmation/shipping_started flags are required independently. An explicit arm_solapi_from_now checkpoint marks prior pending confirmations historical and suppresses prior pending shipping notices before enabling. Existing accepted/unknown evidence is never reset. Do not surprise-backfill historical orders.

DEV sends only to its fixed test recipient after authoritative customer/order/phone ownership lookup. Other recipients are suppressed. Cancelled/returned orders do not get deposit instructions; already-paid confirmations omit the bank/deposit request. Shipping requires native paid/shipped guards and includes carrier/tracking. Existing Twilio OTP credentials and behavior remain unchanged.

## Activation after carrier resolution

1. Preserve private keys and resolve sender blocking with its carrier, or register an eligible alternative sender.
2. One fresh, journaled manual test; verify final handset-delivery state and user receipt.
3. Snapshot existing SMS journals, run explicit future-only arm checkpoint while disabled, then enable only authorized DEV order/shipping purposes.
4. Verify one new confirmed DEV order and one paid shipment. Phone authentication migration and PROD customer-recipient composition require their own implementation/activation.

Current flags remain false. Prepared code does not imply automatic service activation.

## Validation

225 related provider/outbox, dialogue/bridge/Codex, native order/stock/return and isolation regressions. Provider tests use fake sessions; one live connectivity submission failed with the diagnosed carrier code. No real order/payment/stock changes, no account data in public output or Git. Original dirty work preserved.

Official references:
- https://solapi.com/developers/api/messages
- https://solapi.com/developers/api/authentication-api-key
- https://solapi.com/developers/api/msg-getList
- https://solapi.com/guides/message-status-codes

Activation checkpoint 2026-10-12 07:50 KST: DEV API 3433cccdc3496e4feeed6b5826288e4d7b7aaf54 is active; order_sms=CONFIGURATION_REQUIRED and both SOLAPI/order-notification enabled flags remain false. Qwen operator bridge and Codex draft service remain healthy. Backup: com.aicontrolcenter.dev-order-api.plist.backup-20261012-075013. PROD is unchanged by this SMS task. Next gate is sender-carrier 3113 resolution, one successful final delivery/handset test, then future-only DEV activation.
