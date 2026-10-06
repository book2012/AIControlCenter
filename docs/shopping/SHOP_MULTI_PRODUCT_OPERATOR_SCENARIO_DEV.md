# DEV multi-product storefront and operator scenario

## Scope
This milestone connects five immutable demo storefront identifiers to five isolated DEV WooCommerce variable products and provides idempotent synthetic operator acceptance data. PROD, real payment, carrier APIs and SMS verification are not mutated.

## Orderable DEV products
- `oc-demo-top-0001` -> Woo product 10, 소프트 린넨 블라우스
- `oc-demo-bottom-0001` -> Woo product 17, 내추럴 와이드 팬츠
- `oc-demo-outer-0001` -> Woo product 21, 소프트 니트 가디건
- `oc-demo-dress-0001` -> Woo product 25, 내추럴 린넨 원피스
- `oc-demo-bag-0001` -> Woo product 29, 미니멀 숄더백

The homepage remains the canonical visual storefront. Cards preserve the existing image/hashtag-only contract. Only the five allowlisted DEV product detail pages expose the `DEV 문의·주문하기` CTA, which routes through `/dev-order/product/{demo_id}` to the private Woo product mapping.

## Synthetic operator acceptance data
Synthetic verified phone fixture: `01000000000`. No SMS provider call is made.

Orders:
- #31: 확인대기
- #32: 발송대기
- #33: 배송중, multi-line order
- #34: 처리완료 (delivery complete)
- #35: 거절

#34 also has one synthetic return request. Three synthetic inquiries were created: two operator-pending and one safe auto-learning approved answer. Order and inquiry Telegram outboxes were drained successfully.

## Status presentation
A confirmed order is presented as:
- `READY_TO_SHIP` -> 발송대기
- `SHIPPED` -> 배송중
- `COMPLETED` when fulfillment is `DELIVERED` -> 처리완료

Review states such as 확인대기 and 거절 remain unchanged.

## Admin incident fix
The DEV admin page previously remained at “불러오는 중…” because Python interpreted JavaScript `\n` literals as physical newlines inside quoted JS strings. The HTML source now emits escaped JavaScript newline sequences. The regression test asserts those sequences are present.

## Validation
- Storefront focused: 51 passed.
- Storefront combined regression: 150 passed.
- Admin/order/after-sales focused: 29 passed.
- Five demo-ID redirects resolve to the intended DEV Woo products.
- Telegram order outbox: pending/claimed 0 after dispatch.
- Admin API displays #31-#35 with the intended mixed states.
- PROD mutation: none.
## Live DEV activation
The immutable Homepage DEV release sourced from commit `d6a12423230d93c90057ad89dec1d3e6b3598ff4` is active on port 18080. The listener cwd matches that release directory. Live homepage smoke preserved the 24-card feed and showed no order CTA on the feed itself; each of the five allowlisted product detail pages exposes the DEV inquiry/order CTA and redirects to Woo products 10, 17, 21, 25 and 29 respectively.

Headless Chrome rendered the operator admin page with synthetic orders #31 and #34, displayed `처리완료`, and no longer remained on `불러오는 중…`. External DEV remains protected by the existing Basic Auth edge (unauthenticated smoke: HTTP 401).

