# Telegram product management — DEV

The user authorized natural-language stock, regular price, discount, hide and restore commands through the existing operator bot. Product additions remain a GPT workflow. The examples are grammar examples; they are not silently applied to the live catalog during development.

## Authority and scope

Only trusted Bot API getUpdates messages from the existing fixed operator chat and user allowlist, with chat.type=private and is_bot=false, reach the product operator. The existing durable Telegram cursor rejects duplicate updates before dispatch. Existing order confirmation, inquiry answers and aftersales routing remain intact. There is no webhook, browser management endpoint, generic shell dispatcher, product creation or permanent deletion. The default core integration has no product operator; only the isolated DEV composition supplies one.

The Python adapter resolves exact names from the 19 uploaded records. Duplicate names, unknown options, incomplete multi-color/multi-size stock commands, mixed actions and invalid amounts deny without mutation. Stock is an absolute quantity for one exact variation, 0–9999; price is 1–10000000 KRW. Multiple-color products require a color for stock commands; single-color products infer that color. Regular price, sale, hide and restore affect the whole product. A regular-price change clears the prior discount; discount cancellation preserves regular price. Sale must be below regular price.

Examples:
- 카멜 벨티드 롱 코트 L는 재고 없음으로 변경
- 베이직 하이넥 니트 네이비 M 재고 3개로 변경
- 브라운 싱글 롱 코트 가격 200000원으로 변경
- 베이직 하이넥 니트 는 50000으로 할인
- 베이직 하이넥 니트 할인 취소
- 브라운 싱글 롱 코트 제거
- 브라운 싱글 롱 코트 다시 공개
- 베이직 하이넥 니트 재고 확인
- 상품관리

## Durable mutation and Commerce ownership

A private Mac SQLite command journal records update ID, canonical command digest and PENDING before I/O. The provider is fixed to colima-aicontrolcenter-commerce / aicc-order-dev-wordpress-1 and checks database aicc_order_dev, isolated container project/volumes, bound provider IDs, aicc-dev SKU, catalog metadata, variation attributes, managed stock and disabled backorders. Inputs are structured base64 JSON in a fixed PHP program, never interpreted as code.

The Woo transaction shares the aicc_dev_stock_confirmation lock with order-confirmation inventory reduction, validates InnoDB, and commits an update-ID/digest receipt alongside mutation. A replay reads the committed receipt and cannot reset stock changed by later orders. Unknown transport outcomes retain PENDING; the worker reconciles the same provider receipt key and sends a completion notice once the result is known. A digest conflict denies. Reply delivery remains informational: unknown message-delivery results do not repeat the business mutation.

Sale changes all active variation sale prices, clears scheduled sale dates, synchronizes parent price lookup and adds the owned SALE product tag. Price reset/discount cancellation removes only this owned tag. Hidden products become draft; show restores publish. Their product IDs, images, inventory, order history and other tags remain intact. DevCatalog denies unpublished parents before quotes or checkout.

## Read projection and storefront

Woo remains authoritative for price and stock. After a successful command, the operator atomically publishes a private, credential-free public-data JSON projection. It includes exactly the 19 uploads, canonical catalog SHA256, DEV identity, price/discount/publication state and complete known variation quantities. The preview adapter rereads the projection on file version changes, validates its scope, fields, prices, quantity bounds and private file ownership/permissions, and rebuilds its read model without deployment or per-view Woo HTTP. Corrupt or missing previously published projections fail closed. Source catalogs, galleries and private runtime bindings are not rewritten.

SALE feed membership requires an actual sale price; obsolete sample collection membership cannot fabricate a discount. Cards display #SALE; details show sale price and original price. Hidden products disappear from listing/search/HOT/SALE and return 404 on details. Price/stock changes appear on the next page load. Remaining Woo stock is refreshed at most every 30 seconds; quotes and checkout always query current Woo state. Server-rendered feed retries reload the authoritative projection instead of clearing SALE to legacy demo results. The existing no-store DEV response boundary is preserved.

## Validation

306 Python regressions cover operator grammar, ambiguity, operator/private-chat auth, update replay, uncertain provider commit recovery, projection failures, dynamic price/SALE/hide/restore, hidden checkout denial, existing order/inquiry/aftersales and storefront flows. Legacy UI assertions were aligned with the already-authorized cart; provider fixtures now explicitly declare publish status.

A disposable real Chrome harness runs six trusted fake Telegram commands and verifies SALE/original price, price change, exact size sold-out control, hide/restore with images, discount cancellation and mobile layout. Combined-option cart browser checks also pass. The real isolated Woo handler is separately exercised for all six mutation paths with enforced SQL ROLLBACK; catalog snapshots remain identical. No real order, SMS or example product mutation is committed by these tests.

## Activation

Commit/push and clean/upstream verification precede activation. Both homepage and order API use the same immutable commit-addressed DEV release. Preserve the old current manifest and configs, verify listener ownership/cwd, stop only owned DEV processes, release the old poller lease and require DEV/RUNNING poller plus product_management health. The first sync is read-only and publishes actual current Woo state. Rollback restores the old manifest and restarts the owned previous API; the new command journal and Woo receipts remain durable for later reconciliation. PROD, Caddy, Ubuntu and unrelated dirty work are outside scope.

## Outer inventory list extension

아우터 리스트 / 아우터 목록 resolve to a read-only category query before exact product-name parsing. One fresh validated Woo snapshot supplies all five uploaded outers, including exact size/color quantities, 품절 (0개), and [숨김] markers. No provider apply call or mutation-journal entry occurs. The complete current response fits Telegram's 4096-character bound. Private operator auth and durable cursor still apply. Six new regressions exercise grammar, current quantities, hidden markers, category exclusion, empty category, trusted delivery and duplicate suppression.

The extension changes only the operator runtime; its immutable DEV API release can advance independently while the existing homepage reads the unchanged projection schema. Preserve existing live command history and user-modified prices/stock/publication state during activation.

## List price extension

Each outer block includes price and sale status above the existing variation stock rows. A non-null validated sale price displays SALE · 정상가 X원 → 할인가 Y원; otherwise 가격 X원 · 세일 아님. 정상가 denotes the regular selling price, not purchase cost, which this catalog does not contain. A fresh Woo snapshot ensures price changes and cancelled discounts are visible on the next list request. This remains a read-only operator query and preserves the private-chat, no-PROD and API-only immutable-release activation boundaries.

## Category list and search extension

Read-only list grammar supports the six canonical categories, the forward-compatible empty MEN category and ALL. Korean and existing storefront English labels resolve to explicit category keys; unrecognized labels return supported categories. A trailing keyword filters exact product names by case-insensitive substring inside the selected category. Stock, price and sale values still come from one fresh scoped Woo snapshot; query text never becomes a mutation. Empty categories/results are explicit, and existing private operator routing retains priority. The current full-catalog response remains under Telegram's character limit.
