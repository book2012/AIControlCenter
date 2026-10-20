# DEV Telegram → Codex product intake

Status: source implementation, not activated. This increment connects the DEV operator's private `papachichi_bot` text messages to the existing isolated Codex product draft worker. It does not create WooCommerce products.

## Operator flow

1. Tap `➕ 상품 등록 안내`, then send `상품 등록: 상품명, 가격, 색상, 사이즈, 옵션별 실제 재고` or `상품 등록 초안: ...`. Missing facts can be marked `확인 필요`.
2. The bot returns an eight-character job ID. `상품초안 #ID` shows its state; `상품초안 목록` lists the operator's recent jobs.
3. The existing Codex worker creates exactly one schema-checked DEV draft in a pinned feature worktree. Completion or failure sends a private notice once. The worker cannot register products or activate a release.
4. The DEV admin page `/dev-order/admin` remains the review surface. There the operator confirms price, options, stock, the five required image roles and image provenance. Existing read-only preflight and exact-name confirmation guard the DEV WooCommerce registration. Homepage publication remains a separate release.

## Boundaries

The independent DEV bot validates the fixed private chat and user allowlist before the signed Unix-socket bridge. The durable bridge update ID and actor-scoped dialogue journal prevent replay; an uncertain claim requires inspection. Product jobs use the existing `website_jobs` table and `PRODUCT_INTAKE::` prefix, so the current Codex worker handles them without a shell command in Telegram. Status queries are scoped to the Telegram actor. Browser-created jobs keep their web-only notification behavior.

No bot photo transfer or Telegram registration confirmation is included yet. Telegram `getFile` ingestion would need bounded private storage, file signature and provenance checks, media-group handling and a safe review UI. Do not claim that a Telegram photo alone is enough to publish a product. The existing five-image registrar still requires reviewed source/media and separate immutable DEV storefront activation. PROD and customer bots remain outside this increment.

## Validation and activation

Run the focused conversation, bot callback, Codex worker and intake tests. Activate only through the existing immutable DEV API/poller procedure after a clean committed revision and runtime check. A synthetic Telegram request should yield one Codex job, one notice and zero WooCommerce writes. No live product registration is needed for this gate.
