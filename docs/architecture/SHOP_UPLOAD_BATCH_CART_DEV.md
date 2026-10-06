# SHOP_UPLOAD_BATCH_CART_DEV

Reviewed 18 source photos as 17 new products (the two brown-coat photos are one product). Together with the two existing coats, uploaded-only storefront has 19 products. New prices are user-authorized temporary values; unknown size/physical inventory remains explicitly pending with zero sellable stock. Front model thumbnails, original-based transparent retouches and other model views share the existing manifest/SHA boundary. Order controls sit below SIZE/COLOR with compact buttons; the top-right cart opens a dedicated page with product names/options, quantity edits, removal and session navigation persistence. Server quotes and final checkout revalidate authority; cart edits invalidate prepared review and pending durable operations remain protected. PROD is outside scope.

| Product | Temporary KRW | Color options |
|---|---:|---|
| 블랙 자수 니트 베스트 | 79000 | 블랙 |
| 블랙 위빙 숄더백 | 129000 | 블랙 |
| 브라운 위빙 버킷백 | 98000 | 브라운 |
| 코랄 페이즐리 롱 원피스 | 149000 | 코랄 |
| 베이지 블랙 패턴 원피스 | 159000 | 베이지·블랙 |
| 블랙 플라워 자수 블라우스 | 89000 | 블랙 |
| 블랙 레이스 롱 원피스 | 129000 | 블랙 |
| 화이트 핀턱 블라우스 | 89000 | 아이보리 |
| 화이트 그래픽 브이넥 니트 | 99000 | 화이트 |
| 베이지 체크 스퀘어 스카프 | 59000 | 베이지 |
| 네이비 스트라이프 롱 원피스 | 99000 | 네이비·화이트 |
| 데일리 스트라이프 셔츠 | 79000 | 스카이블루, 네이비 |
| 레드 퀼팅 후드 재킷 | 139000 | 레드 |
| 차콜 와이드 슬랙스 | 89000 | 차콜 |
| 베이직 하이넥 니트 | 69000 | 그레이, 아이보리, 브라운, 네이비, 블랙 |
| 브라운 싱글 롱 코트 | 189000 | 브라운 |
| 카멜 숄카라 벨티드 코트 | 229000 | 카멜 |

## Authority and storage

AIControlCenter remains the control plane. WordPress/WooCommerce stores DEV product and variation records in the isolated aicc-order-dev compose project; only the explicit --apply-dev registrar can mutate that namespace. It asserts DEV container labels, dedicated volumes/network, database name, reviewed metadata, stock pending/zero, media hash and option identities. Default invocation is read-only. Existing product/variation state is validated on replay rather than reset.

runtime.batch-candidate.private.json is staged with permissions 0600; it does not affect the current API until deliberate release activation. Existing hidden sample bindings remain available to historical orders. They are excluded from customer listings and the public cart metadata endpoint. Originals are retained under uploads/source and never displayed as untreated screenshots. The 51 generated gallery assets and 17 representative JPEGs are hash-bound. AI views are explicitly labeled, and styling items are excluded from sale.

The same aicc-guest-cart-v1 sessionStorage line schema spans product pages and the dedicated cart page. Only product/variation IDs and bounded quantities are stored; no PII or authority is persisted there. Anonymous GET metadata supplies names and option labels. Checkout quotes and final preparation fetch current provider price, options and stock. Editing the cart clears the prepared review. An existing durable operation blocks cart mutations and additional checkout until its state is resolved. Phone verification, address lookup, CSRF/session binding, durable order ledger and Telegram operator review remain unchanged.

## Validation

- 190 Python tests across upload visibility/media/options, inquiry history, guest quote/checkout/phone, canonical catalog resolution and Telegram review.
- Four isolated Chrome harnesses: nine dedicated-cart checks, seven shared-chat/history checks, anonymous inquiry/cart/phone gate, and full fake phone/address/order/operator-confirmation flow.
- Browser tests send zero external provider requests. The full checkout harness performs one fake writer create and two fake Telegram messages.
- JavaScript syntax, Python compilation and Git whitespace checks.
- DEV registrar plan: 17 products, temporary prices and pending zero stock. DEV apply: 17 created; candidate binding staged.
- Read-only before/after commerce snapshots preserve all seven pre-existing product bindings and eight orders.

## DEV activation and rollback

After feature commit/push, archive the clean revision into the existing homepage-dev release root. Preserve current homepage manifest and API CWD, plus the private runtime mapping. Stop only the verified owned DEV API listener, install the staged mapping atomically, and start the API from the new immutable release. Require health/poller RUNNING, all 19 uploaded product embeds and metadata, pending-stock denial and media hashes. Then switch only the DEV homepage manifest and terminate its verified owned listener so its supervisor restarts. Require the new CWD, 19-product listing, dedicated cart route, compact option-adjacent controls and loading images.

On API failure, restore the backed-up private mapping and restart the prior API release; leave the homepage manifest unchanged. On homepage failure, restore its prior manifest and restart the owned homepage listener. No Caddy, PROD application/database, production branch or external provider mutation is part of this activation. PROD promotion remains separately prohibited until explicitly authorized.

Actual size choices and physical stock counts for the 17 new products remain the next business input. Five knit colors and two shirt colors are presentation/variation options, not invented sellable inventory.
