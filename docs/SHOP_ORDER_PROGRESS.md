# Non-SMS order workflow progress

Updated: 2026-10-11 (Asia/Seoul). Current completed stage: 4 (code/tests). Stage-4 DEV API/presentation is active at 4473f1a (verified during this stage-5 preparation). Stage 5-1 private receiver/forwarder preparation is implemented; shared Telegram activation remains separately gated.

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

DEV API release ab434b9478498180345538d3141ce853048a2757 activated 2026-10-11 22:38:50 KST. operator_bridge=RUNNING, poller=EXTERNAL, product_management=RUNNING. An unsigned socket request was rejected without invoking any command. Private receiver key/config is 0600; no second getUpdates consumer. Homepage remains on 4473f1a because no UI change. Shared PROD bot and SMS remain unchanged. DEV LaunchAgent backup: com.aicontrolcenter.dev-order-api.plist.backup-20261011-223850.
