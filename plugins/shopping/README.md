# Agachichi Commerce

쇼핑몰과 판매용 테마

This is a platform plugin boundary record, not a ChatGPT plugin ZIP or WordPress plugin.
The manifest is descriptive data, never executable configuration or authorization.

## Components

- 상품 조회 — `VALIDATION_ONLY`
- 주문 조회 — `BINDING_REQUIRED`
- 회원 세션 조회 — `BINDING_REQUIRED`
- 알림 준비 상태 — `BINDING_REQUIRED`
- Atelier WordPress 테마 — `SEPARATE_PRODUCT`
- 실제 거래·문자·텔레그램 — `NOT_CONNECTED`

## Source ownership

- `core/shopping`
- `core/modules/shopping.py`
- `core/modules/shopping_bindings.py`

## Detach

새 플랫폼 요청 차단, 등록 작업 drain, 등록 자원 close; WooCommerce 데이터·독립 매장은 유지

The runnable adapter source now lives under `src/aicc_plugin_shopping`. Build its installable wheel with `python -m scripts.build_plugin_wheels`. It requires the compatible AIControlCenter host; it is not a standalone application or a complete legacy-domain extraction. See docs/architecture/PLATFORM_PLUGIN_PACKAGES.md.
