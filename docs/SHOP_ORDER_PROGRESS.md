# Non-SMS order workflow progress

Updated: 2026-10-11 (Asia/Seoul). Current completed stage: 3 (code/tests). Next feature stage: 4. DEV API/presentation activation checkpoint is stage 5; live shared Telegram remains unchanged.

| Stage | Scope | Status | Evidence / remaining gate |
|---|---|---|---|
| 1 | Woo stock concurrency and exactly-once cancellation primitive | Complete | Synthetic isolated Woo probe passed; fixtures cleaned |
| 2 | Core cancellation guards and ambiguous-outcome reconciliation | Complete in code/test | 111 tests; Chrome checkout regression; actual Woo read-only receipt verification |
| 3 | DEV Telegram commands and customer cancellation presentation | Complete in code/tests | Order-number and phone commands, allowlist, duplicate/update replay and no deposit guidance tested; actual shared bot remains on old PROD release |
| 4 | Return received/inspected restoration | Pending | Return approval must not restore inventory; paid refunds require separate settlement records |
| 5 | Full workflow regression and DEV activation | Pending | Per-stage commits are pushed; stage-3 DEV API and presentation activation follows this commit; full workflow/return validation remains pending |
| 6 | PROD promotion | Pending authorization | Existing PROD Telegram consumer must not be updated implicitly |

## Stage 2 behavior

Unpaid confirmed orders may be cancelled only before shipping. A committed SENDING cancellation record freezes payment and shipping before Woo is called. Successful bound Woo receipts complete CANCELLED. Timeouts or invalid receipts persist UNKNOWN; no automatic write replay is allowed. Explicit reconciliation only reads the existing Woo receipt and verifies order/tag/digest/items/status/reduction flags. Missing proof leaves the order frozen for investigation. Restart and duplicate cancellation preserve the completed receipt. Paid orders are blocked for refund review. No customer or Telegram command is enabled yet.

## Hold / boundaries

SMS is held. Production code/configuration and real customer orders are unchanged. Synthetic Woo probe is DEV only and cleans its own tagged orders/product. The existing original dirty working tree remains preserved.

## Stage 3 commands and deployment boundary

- `주문취소 #15` / `01012345678 주문취소 #15`: confirmed, unpaid, not-shipped cancellation only.
- `취소확인 #15` / `01012345678 취소확인 #15`: read existing Woo cancellation receipt; never resend restoration.
- Phone-only selection refuses ambiguous orders and mismatched phone/order ownership.
- Customer lookup and chatbot notices show CANCELLED or CANCELLATION_PENDING and suppress deposit/account guidance. Late operator confirmation notices honor cancellation state.
- DEV runtime explicitly composes the stock cancellation provider. The shared PROD Telegram consumer is pinned separately; updating DEV API alone does not activate bot commands. Do not spawn a second getUpdates consumer.

Validation: 116 regression tests including five new cancellation operator/customer tests, isolated Chrome customer-order states and dedicated checkout regression. No live Telegram/SMS sends or PROD mutations.
