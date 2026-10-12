
# SHOP Manual Refund Completion Records — DEV

This feature records an operator attestation of an already completed bank transfer. It has no bank/payment-provider API and cannot transfer or refund money. It is enabled explicitly only in DEV composition; default shared Core/PROD composition remains disabled.

## Operator workflow
After a RETURN case has been approved, physically received, inspected as resalable and inventory restoration verified, send:
`환불완료 #a1b2c3d4 58000원 증빙 BANK-20261012-001`
The DEV dialogue asks for confirmation and states that only a record will be stored. Reply `응` only after verifying the transfer and evidence. Missing case/amount/evidence are requested. Exact formatted requests do not rely on AI parsing; natural requests may use Qwen with bounded data. Generic money transfer requests have no executable handler.

## Durable boundaries
manual_refunds is private SQLite, one immutable record per case/order, unique evidence reference, recording actor/update/time. Only the full authoritative KRW order amount is supported. Different repeated evidence/amount is rejected; concurrent identical confirmations preserve the original receipt. A completed physical return is required. Payment remains PAID as historical inbound payment; return remains RETURN_RESTOCKED, and refund is a separate RECORDED projection. No stock/provider operation occurs during record creation.

## Customer view
Authenticated owned-order lookup exposes amount/currency/recorded timestamp but omits evidence and operator identity. Customer notices and order page show 환불완료 and amount. Operator list/status shows 환불완료 기록; return list retains physical return state plus refund record label. No pending deposit instructions after refund. No new public refund-write endpoint exists.

## Validation 2026-10-12
160 related tests passed, including exact full amount, DEV feature gate, approval binding, invalid actor/evidence, concurrent duplicate/restart, record conflict/evidence reuse, authenticated lookup and evidence privacy. Real headless Chrome on isolated loopback rendered refund status/amount and consistent case row; no external messages/providers. Live Qwen parsed a completion-record request; a money-transfer request failed closed with no execution. This is not proof of a real bank transfer.
SOLAPI one authorized DEV test again reached final 3113. Fixed classifier: 3000 is carrier-processing ACCEPTED, not failure; 2230 is a definitive internal error. SMS auto flags remain false.

## Remaining
Partial refunds, pre-shipment paid cancellation/refund workflow, non-resalable return disposition, record correction/void audit and replacement exchange inventory are not supported in this release. PROD adoption and human acceptance are separate.

Independent DEV bridge cursor hardening: reads/aftersales no longer advance legacy ledger cursor. Order review decisions allocate a monotonic local ledger ID at or above the historical offset, while authenticated bridge original update IDs govern replay. No cursor rewind; restored/new bot commands cannot be incorrectly suppressed by an old shared-bot diagnostic offset. Real isolated SQLite ledger regression verifies confirmation guard once across retry/restart.

Final related regression: 161 passed after independent cursor fix; immutable DEV API and DEV homepage refund UI verified, no live refund records created. SMS remains disabled with latest test3113.
