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

## Domain package 0.2.0

Product/ProductVariant and the pure order domain, read port and OrderService now live in this package. `core.shopping.models` and `core.shopping.order_core` re-export the identical classes for compatibility. Domain imports require no host/HTTP framework; HTTP adapters still use explicit host services. See [ownership and verification](../../docs/architecture/SHOPPING_DOMAIN_PACKAGE_02.md).

## Catalog package 0.3.0

Catalog service, read ports, public settings, response models, mock adapter and bounded read health/telemetry now live here. Construct the service with explicit public settings and catalog port; it does not read host settings or credentials. The host keeps provider/secret composition and authenticated storage. See [catalog extraction and evidence](../../docs/architecture/SHOPPING_CATALOG_PACKAGE_03.md).

## WooCommerce product-read boundary 0.4.0

Product normalization/list/detail/health now use an explicit product-read port and strict authorizer in the plugin. Host signing, credentials, transport and non-product scopes remain outside it. See [ownership and 889 passing checks](../../docs/architecture/WOOCOMMERCE_PRODUCT_PLUGIN_04.md). This Python package version is unrelated to the Atelier theme release.

## Current candidate 0.5.0

Identity/session/auth/persistence/migration/inquiry and remaining WooCommerce read
mapping now live in this wheel. Existing-store resources support explicit
start/close after leased-work drain, without attach-time migration. Host contacts,
credentials, signing/transport, schema loading and authority remain outside it.
Fresh installed-plugin checks: 185 passed; expanded related checks: 2,415 passed.
No live provider binding or production switch.
See [current scope and evidence](../../docs/architecture/SHOPPING_STORAGE_PROVIDER_PACKAGE_05.md).

## On-demand runtime

Shopping resources were paused by explicit user instruction on 2026-11-03.
The reviewed operator-local controller can restore the same production containers
and launchd generation; DEV/QA remain off. Default commands only print plans.
[Commands and safeguards](../../docs/architecture/ASSISTANT_PRIORITY_ON_DEMAND_SHOPPING_01.md).
