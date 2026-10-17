## 2026-10-17 — DEV 관리자 주문 챗봇과 Codex 상품 intake 활성화

Immutable DEV API release `9c0784cdcb71c1bee8e4d6a98c3e3520d6106cf8` is active. `/dev-order/admin` combines orders, on-demand delivery details, aftersales/inquiries and operator chat. Same-origin requests are required; Caddy Basic Auth protects the external DEV route. Order chat uses the existing explicit confirmation path. Product intake queues Codex in an isolated worktree; only a schema-checked JSON proposal is shown, with no catalog, WooCommerce, order, or PROD write. A synthetic Codex request generated a review draft. Checks: 60 focused tests passed; page 200, unauthenticated public page 401, same-origin read-only chat 200, health reports `poller=EXTERNAL`. Backup at `AIControlCenterRuntime/dev-order/backups/dev-order-admin-20261017-095343` (private runtime). Existing release 534 remains preserved. Next: reviewed image upload and complete verified spec handoff to the isolated DEV registrar.

# Non-SMS order workflow progress

Updated: 2026-10-11 (Asia/Seoul). Current completed stage: 4 (code/tests). Stage-4 DEV API/presentation is active at 4473f1a (verified during this stage-5 preparation). Stage 5-1 shared relay is active at 0289213 (old-PROD-based isolated relay branch); actual human Telegram and stage 5-2 full order workflow remain pending.

| Stage | Scope | Status | Evidence / remaining gate |
|---|---|---|---|
| 1 | Woo stock concurrency and exactly-once cancellation primitive | Complete | Synthetic isolated Woo probe passed; fixtures cleaned |
| 2 | Core cancellation guards and ambiguous-outcome reconciliation | Complete in code/test | 111 tests; Chrome checkout regression; actual Woo read-only receipt verification |
| 3 | DEV Telegram commands and customer cancellation presentation | Complete in code/tests | Order-number and phone commands, allowlist, duplicate/update replay and no deposit guidance tested; actual shared bot remains on old PROD release |
| 4 | Return received/inspected restoration | Complete in code/tests | Approval/receipt never restore; explicit inspection restores once; ambiguous outcomes read-only reconciled; refund remains separate |
| 5 | Full workflow regression and DEV activation | Pending | Per-stage commits are pushed; stage-4 DEV API/presentation active at 4473f1a; private bridge preparation implemented; shared Telegram/live end-to-end validation remains pending |
| 6 | PROD promotion | Pending authorization | Existing PROD Telegram consumer must not be updated implicitly |

## Stage 2 behavior

Unpaid confirmed orders may be cancelled only before shipping. A committed SENDING cancellation record freezes payment and shipping before Woo is called. Successful bound Woo receipts complete CANCELLED. Timeouts or invalid receipts persist UNKNOWN; no automatic write replay is allowed. Explicit reconciliation only reads the existing Woo receipt and verifies order/tag/digest/items/status/reduction flags. Missing proof leaves the order frozen for investigation. Restart and duplicate cancellation preserve the completed receipt. Paid orders are blocked for refund review. Commands are wired in DEV API code; the live shared Telegram consumer remains pinned to the prior PROD release.

## Hold / boundaries

SMS is held. Production code/configuration and real customer orders are unchanged. Synthetic Woo probe is DEV only and cleans its own tagged orders/product. The existing original dirty working tree remains preserved.

## Stage 3 commands and deployment boundary

- `주문취소 #15` / `01012345678 주문취소 #15`: confirmed, unpaid, not-shipped cancellation only.
- `취소확인 #15` / `01012345678 취소확인 #15`: read existing Woo cancellation receipt; never resend restoration.
- Phone-only selection refuses ambiguous orders and mismatched phone/order ownership.
- Customer lookup and chatbot notices show CANCELLED or CANCELLATION_PENDING and suppress deposit/account guidance. Late operator confirmation notices honor cancellation state.
- DEV runtime explicitly composes the stock cancellation provider. The shared PROD Telegram consumer is pinned separately; updating DEV API alone does not activate bot commands. Do not spawn a second getUpdates consumer.

Validation: 116 regression tests including five new cancellation operator/customer tests, isolated Chrome customer-order states and dedicated checkout regression. No live Telegram/SMS sends or PROD mutations.

## Stage 4 physical return and stock restoration

`환불승인 #케이스번호` approves the existing RETURN case without refund or stock writes. `반품 회수 #케이스번호` records physical receipt. Only `반품 검수완료 #케이스번호` explicitly attests all returned items passed inspection and are resalable, then restores whole-order stock once. Damaged/non-resalable goods stay at receipt/inspection pending; do not send inspection-complete. `반품 복원확인 #케이스번호` reads the existing bound Woo receipt after an ambiguous result; it does not retry stock writes. Partial returns and exchange replacement-stock movements are outside this release.

Return operations bind order, operation tag, original delivery digest, exact line items and case ID. A unique order-level restoration claim prevents duplicate inventory movements. Restart/replay/concurrent inspection preserve the outcome. Approval and case creation now serialize state changes; historical case access uses exact case filtering. Woo return receipt also blocks later Core confirmation/cancellation from moving stock again. Native Woo order/payment status is not changed to refunded.

Validation: 136 related tests; isolated real Woo concurrent return/replay/receipt-binding checks; customer-order Chrome checks for returned/unknown states; dedicated checkout Chrome regression. Synthetic Woo fixtures cleaned. Customer and operator labels show inspection complete/refund review, never financial refund complete. No external Telegram/SMS messages or PROD writes.

## Stage 5-1 preparation

Opt-in private authenticated DEV receiver and shared-consumer client/composition added. No public route or second getUpdates loop. Shared consumer preserves its existing bot cursor and never falls back to the old embedded DEV handler after a forwarding failure. Receiver activation requires external-consumer mode. DEV receiver is now RUNNING on API release ab434b9; the shared consumer configuration/release is unchanged, so actual bot forwarding remains pending. New independent personal-bot capacity checked locally: qwen3:4b uses ~2.87 GB at context 2048; validated separate no-thinking prefill returns Korean text. New bot credential/allowlist and personal conversation service remain pending.

Validation: 184 targeted order, Telegram, cancellation, return, guest-runtime and isolation regressions passed; diff whitespace and Python syntax checks passed. Socket probes use disposable fake providers. No external Telegram/SMS sends or PROD writes.

### DEV activation checkpoint

DEV API release ab434b9478498180345538d3141ce853048a2757 activated 2026-10-11 22:38:50 KST. operator_bridge=RUNNING, poller=EXTERNAL, product_management=RUNNING. An unsigned socket request was rejected without invoking any command. Private receiver key/config is 0600; no second getUpdates consumer. Homepage remains on 4473f1a because no UI change. At this earlier checkpoint shared PROD bot and SMS remained unchanged. DEV LaunchAgent backup: com.aicontrolcenter.dev-order-api.plist.backup-20261011-223850.

## 2026-10-12 — Shared DEV relay activated

Shared consumer active at 0289213a1ae1aff007edcf9972a0ba7c26651a57; independently pinned DEV API ab434b9. Authenticated local read-only 주문목록 roundtrip passed without advancing the existing DEV cursor or sending a diagnostic Telegram message. DEV receiver and PROD poller/product management RUNNING; DEV/PROD API and PROD storefront return HTTP 200. PROD business modules remain based on 63e0f104; presentation stays 8d6f508; SMS disabled. Existing router/cursor preserved. Backup: prod-commerce/backups/dev-relay-20261012-064125. Actual human Telegram command and full order workflow remain to verify.

## 2026-10-12 — One Telegram greeting across DEV forwarding

Live operator DEV response confirmed the shared forwarding path but exposed duplicated greeting/environment headers. Environment routers now preserve an existing identical header instead of adding another. Nested-router replay and ordinary PROD/DEV reply regressions pass (97 targeted tests on isolated relay branch). Historical DEV fixtures 33/34 have shipment/delivery rows but no payment row; no payment or shipment state was changed.

Human Telegram DEV order-list command was confirmed by the user on 2026-10-12 06:51 KST. Stage 5-1 live forwarding confirmed. Stage 5-2 fresh full workflow remains next.

## 2026-10-12 — DEV Qwen dialogue, reminders and Codex drafts

Natural operator text is locally classified into bounded order/product actions. Actor-scoped dialogue asks for missing targets/options and confirms mutations before existing guarded handlers run. Durable reminders cover approval, order review, deposit and shipping followup without retrying unknown sends. Confirmed website requests start an isolated sandboxed Codex DEV draft and notify review readiness; no automatic deployment. Shared environment memory keeps plain replies in the chosen DEV/PROD conversation and fails closed after expiry. 212 feature regressions, 98 separate relay regressions, seven actual Qwen cases and two real Codex capability probes passed. See [conversation architecture](docs/architecture/SHOP_QWEN_OPERATOR_CONVERSATION_DEV.md).

Priority change: user paused personal assistant work and requested Qwen operator decisions, notices and Codex website improvements. These are a DEV pilot. Fresh full order/return/payment end-to-end and refund-state work remain pending.

## Activation checkpoint — 2026-10-12 07:29 KST

DEV API bb6f09fea12614758f769dcd5247fbc72efffda2 is active with operator_conversation=QWEN_DEV, operator_bridge=RUNNING, poller=EXTERNAL and codex_website_drafts=ENABLED. Shared relay e18d885770f7b97448bfb850ccda76d65ea577ab preserves PROD business base/frontend and enables actor-scoped environment memory. Live authenticated local Qwen order-list and unprefixed task-list roundtrips passed; neither bot cursor advanced and no diagnostic Telegram message was sent. Local model allocation ~3.86 GB at context 8192. Existing real order/payment/stock data was not changed.

Backups: DEV LaunchAgent com.aicontrolcenter.dev-order-api.plist.backup-20261012-072833; shared prod-commerce/backups/conversation-scope-20261012-072905. Human natural-dialogue/confirmation, timed live reminders and a real requested homepage draft remain acceptance checks. No actual customer order mutation is claimed from the local diagnostic.

## 2026-10-12 — SOLAPI order SMS prepared; carrier blocker remains

Added pinned SOLAPI order-confirmation and shipping transport, domestic-number normalization, byte-bounded SMS/LMS and bound final delivery-status receipts. Existing Twilio OTP stays unchanged. DEV activation is explicit/future-only, skips other recipients and never replays failed/unknown sends. 225 targeted regressions passed. One real connection test was accepted but finally failed with carrier code 3113; automatic SMS flags stay disabled pending sender-carrier resolution. See [SMS architecture](docs/architecture/SHOP_SOLAPI_ORDER_SMS_DEV.md).

Activation checkpoint 2026-10-12 07:50 KST: DEV API 3433cccdc3496e4feeed6b5826288e4d7b7aaf54 is active; order_sms=CONFIGURATION_REQUIRED and both SOLAPI/order-notification enabled flags remain false. Qwen operator bridge and Codex draft service remain healthy. Backup: com.aicontrolcenter.dev-order-api.plist.backup-20261012-075013. PROD is unchanged by this SMS task. Next gate is sender-carrier 3113 resolution, one successful final delivery/handset test, then future-only DEV activation.

## 2026-10-12 Stage 2 DEV fulfillment verification
- New isolated journey test links OperatorConversation approval to GuestOperatorAdapter, durable aftersales state and authenticated customer lookup HTTP route.
- Shipping before payment is denied, every mutation requires confirmation, replay applies once, paid/shipped/delivered states match customer API, receipt survives restart, shipping outbox records one event.
- Live isolated DEV Woo stock probe passed: stock 1/two simultaneous orders produces one confirmation, replay does not reduce twice; cancellation and return restoration concurrency/reconciliation boundaries also passed. Synthetic Woo product/orders and probe journal cleaned.
- Related regression: 142 passed. No external Telegram/SMS messages, no real customer order edits, no PROD mutation. Runtime stays dfe5fd0 because this checkpoint changes tests/docs only.
- Remaining acceptance: human storefront/browser flow and new Telegram message roundtrip; real phone/SOLAPI delivery still blocked by 3113. No claim of complete live browser-to-carrier end-to-end validation.
- Next stage: detailed cancellation/return/refund-record workflow, without automatic money transfers.

## 2026-10-12 Stage 3 cancellation and return checkpoint
Isolated dialogue-to-aftersales journeys verify explicit actor-bound approval, one-time unpaid cancellation restoration, receipt-before-inspection, inspection-only return restoration, duplicate command suppression and customer notices without stale bank/deposit instructions. Return restocking preserves PAID and does not claim refund completion or execute payment transfers.
Regression exposed contradictory case decision replies: reversing an approved/rejected case kept its state but reported the requested opposite decision. The durable store now rejects CASE_DECISION_CONFLICT and operator replies state the conflict without claiming success.
146 related tests passed. No real customer orders, provider stock or PROD business data changed in this stage. DEV-only deployment; original dirty work preserved.
Remaining: explicit manual refund-completion record with amount/evidence and customer presentation is not yet implemented; partial refunds and exchange replacement-stock orchestration are also pending. Human browser acceptance and SOLAPI 3113 resolution remain separate.

2026-10-12: DEV manual refund-completion records implemented after verified return restocking; explicit case/full KRW amount/evidence and actor-bound confirmation required. No transfer APIs; customer projection omits proof/actor. Refund order-page UI and operator presentation updated. 160 regression tests + real isolated Chrome passed. SOLAPI retry final3113, auto SMS disabled; processing3000 classifier corrected. See SHOP_MANUAL_REFUND_RECORD_DEV.md.

Independent DEV bridge cursor hardening: reads/aftersales no longer advance legacy ledger cursor. Order review decisions allocate a monotonic local ledger ID at or above the historical offset, while authenticated bridge original update IDs govern replay. No cursor rewind; restored/new bot commands cannot be incorrectly suppressed by an old shared-bot diagnostic offset. Real isolated SQLite ledger regression verifies confirmation guard once across retry/restart.

Final related regression: 161 passed after independent cursor fix; immutable DEV API and DEV homepage refund UI verified, no live refund records created. SMS remains disabled with latest test3113.
