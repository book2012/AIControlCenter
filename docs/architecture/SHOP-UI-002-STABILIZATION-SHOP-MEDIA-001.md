# SHOP_UI_002 stabilization + SHOP_MEDIA_001

2026-09-14. Implementation on the existing dirty tree; no staging, commit,
push, package installation or production activation.

## A. Architecture fix

There is one presentation path: the real Homepage GET routes call the escaped
read-only renderer in `core/homepage/storefront.py`, which uses the injected
canonical ShoppingService and existing response models. Templates contain
presentation slots only. Browser JavaScript enhances subsequent navigation,
canonical reads and history restoration; initial Home/PDP HTML needs no duplicate
browser read. Search owns URL category/q/page state, GET forms and pagination.

The repository-owned `core/homepage/preview.py:create_app` composes a fixed demo
ShoppingService with those exact Homepage and Shopping routers. The focused
fixtures use this same factory. Its middleware accepts only GET preview/catalog
paths, blocks operator/runtime paths, emits the presentation version header and
sets no-store caching. It does not import the production `core.api.app` or build
a production runtime. Canonical Shopping schemas, contracts, adapters and all
92 catalog records are unchanged.

The launcher `scripts/preview_orange_coco.py` isolates inherited configuration
and .env loading, binds only loopback, and enables uvicorn's existing Python
reload support. Template and media files are read from the repository. The
read-only `scripts/check_orange_coco_preview.py` checks actual HTTP responses,
version headers and template absence, rather than assuming fresh fixture tests
prove that the long-lived preview process is current.

## B. Verified placeholder root cause

The existing loopback listener was PID 19878, started on September 14 at
08:56:56, running the reviewed temporary demo-preview script. Those temporary
launchers imported Python route functions once and called uvicorn without
reload. The loaded old route still used the static HTML file helper. New
server-rendered template files on disk were therefore sent directly to clients
by old in-memory static handlers.

Direct GET evidence from `http://127.0.0.1:18080` before replacement:

- `/homepage/storefront`: **200**, response exactly equal to the current raw
  `core/homepage/ui/storefront.html` file, with literal template placeholders.
- `/homepage/storefront/search`: **404**, although this route existed in the
  current source. This confirmed that the running process had stale routes.
- Fresh in-process tests passed because they imported the current routes; they
  had not validated the long-lived dev listener.

The static helper now rejects storefront HTML templates. The renderer rejects
unresolved delimiters. Literal braces in canonical text/query values are HTML
entities, retaining the exact visible text without raw template delimiters in
HTML source. Home, Search and known/unknown PDP responses are explicitly tested.

A new preview was first validated on 127.0.0.1:18081. A guarded local switch
rechecked all seven HTTP checks, PID 19878's exact temporary-preview command
and its loopback 18080 listener, then sent SIGTERM only to that old demo process
and started the reviewed repository launcher on 18080. The temporary 18081
preview was stopped. Caddy was neither edited nor reloaded. Production processes,
production/current, DNS, launchd and Ubuntu were not changed or accessed.

## C. Routes and actual HTTP validation

| Path | Local dev result |
| --- | --- |
| `/homepage/storefront` | 200, rendered Korean home, eight cards |
| `/homepage/storefront/search` | 200, rendered listing, twelve cards |
| `/homepage/storefront/search?category=women-tops&page=2` | 200, preserved state |
| `/homepage/storefront/product/oc-demo-top-0001` | 200, canonical detail |
| `/homepage/storefront/product/no-such-product` | 404, bounded Korean page |
| `/homepage/assets/storefront/hero-boutique.jpg` | 200, local JPEG |
| `/shopping/products/oc-demo-top-0001` | 200, unchanged demo JSON contract |

All local responses carry `X-Shop-Presentation: SHOP_UI_002_SSR_MEDIA_001`.
The same seven checks passed on the temporary validation port and final 18080
upstream. The three required presentation pages contain neither `{{` nor `}}`.

The user-provided external dev origin is `https://dev.bokstory.duckdns.org`.
Its unauthenticated HTTP check received **401**, exit 1. Repository Caddy source
has an authentication directive for that dev site. The authentication boundary
was left intact; no credentials were read or printed. Authenticated external
verification is **NOT_RUN**. This is separate from successful local-upstream
verification; an external 200 or browser visual pass is not claimed.

## D. Navigation

All category, collection, card, pagination and return links are real anchors in
the served HTML. Home category links use supported canonical slugs, resolved to
canonical IDs for Shopping searches. All products uses `/homepage/storefront/search`;
NEW and BEST use `?category=new` and `?category=best`. Cards link to the real
product route with a bounded return URL. Native GET search and pagination
preserve category/query state. JavaScript cancellation, stale-response guards,
Back/Forward restoration and exact decimal formatting remain intact.

Only canonical NEW/BEST membership supplies previews and badges. No in-stock-first
or featured recommendation label, HOT promotion, discount/review invention,
commerce writes, persistent storage, CMS browser access or remote image proxy
is introduced. PDP descriptions remain safe text, with canonical price,
availability and the purchase-unavailable notice.

## E. Visual changes

The header now centers ORANGE COCO and the Korean subtitle, with a functional
search anchor. The page retains ivory/cream, cocoa typography and restrained
orange accents. The hero uses the new warm orange-lit clothing boutique image
with a fictional adult female model, cream/orange racks and soft daylight.
Its visual height is 180px mobile and 260px desktop. Photography remains first
on cards, with slightly quieter corners and the responsive 2/3/4 grid.

Primary copy remains “일상에 가볍게, 작은 온기를.” Secondary copy is now
“오늘도, 조금 더 사랑스러운 당신에게.” Sections read “NEW 신상품” and
“BEST 인기상품”. Home keeps four products per section, category shortcuts and
one clear “전체 상품 둘러보기 · 검색” link; no discovery form appears on home.
Search and read-only PDP remain separate pages.

## F. SHOP_MEDIA_001 status

**Hero: 1 completed. Product images: 7 / 92 replaced, exactly 85 pending.**

The hero is brand-owned at
`brands/orange-coco/assets/media/storefront/hero-boutique.jpg`, served by a fixed
Homepage GET route independent of plugin deployment paths. Seven independently
generated portrait images cover all eight home slots, since top-0004 belongs
to both canonical collections. Replaced product IDs are top-0001, top-0002,
top-0003, top-0004, top-0008, top-0012 and top-0016 (all prefixed `oc-demo-`).
Their existing JPEG target filenames and repository/static photo routes remain
unchanged. None of the remaining 85 images was deleted or relinked.

The built-in `image_gen` tool produced the eight completed assets. All were
visually inspected for the requested warm editorial direction, fictional adult
models and absence of visible third-party branding. Selected outputs were
encoded as real JPEGs via local `sips` formatOptions 88. No packages were installed.

The deterministic [current media manifest](../../brands/orange-coco/assets/media/SHOP_MEDIA_001.json)
contains every exact completed/pending target, remaining candidate path,
checksum, canonical product reference and full prompt/tool provenance for
completed assets. Existing plugin `asset-manifest.json` entries identify the
seven replacements as generated; old Pexels credits remain only as previous
provenance. The prior SHOP_UI_002 JSON remains the pre-swap checksum baseline.
[Brand media instructions](../../brands/orange-coco/assets/media/README.md)
describe the remaining batch workflow. No canonical API field was added for
image-specific styling or product attributes.

## G. Exact validation

- Focused suites: **92 passed**, 5 existing deprecation warnings, 0.98s, exit 0.
- Relevant Homepage/Shopping regressions: **409 passed**, 22 existing deprecation
  warnings, 2.93s, exit 0.
- JavaScriptCore pure helper checks: **40 passed**, exit 0.
- JavaScript syntax: **2 passed**, exit 0 (`storefront.js` and browser runner).
- Offline export: **592 canonical/static responses**, exit 0; every exported
  HTML page asserts no raw template delimiters and the current version header.
- Live HTTP: **7 / 7 passed** on 18081; **7 / 7 passed** on final 18080.
- External dev HTTP: **BLOCKED — 401 authentication**, exit 1.
- Playwright: **NOT_RUN**. Node is absent from PATH and Python Playwright is not
  installed. No browser package or browser was installed/launched.
- `git diff --check`: PASS; all 24 untracked files checked separately without staging.

Focused command:

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_shop_ui_001_storefront.py tests/test_shop_ui_002_storefront.py \
  tests/test_shop_ui_002_preview.py
```

Regression command:

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_homepage_api.py tests/test_ui_01_homepage.py \
  tests/test_homepage_projection.py tests/test_homepage_status.py \
  tests/test_homepage_shopping_dashboard_contracts.py \
  tests/test_shopping_api.py tests/test_shopping_catalog.py \
  tests/test_shopping_categories.py tests/test_shopping_featured.py \
  tests/test_shopping_search.py tests/test_shopping_demo_adapter.py \
  tests/test_shop_api_read_001.py tests/test_shop_api_read_002.py \
  tests/test_shop_api_read_003.py tests/test_woocommerce_adapter.py \
  tests/test_shopping_woocommerce_normalization.py \
  tests/test_shopping_woocommerce_read_transport.py tests/test_shopping_factory.py \
  tests/test_shopping_read_only_ports.py tests/test_shopping_external_read_policy.py \
  tests/test_dashboard_shopping_management.py \
  tests/test_shopping_management_read_model.py \
  tests/test_shopping_adapter_contract_isolation.py \
  tests/test_shopping_commerce_adapter_contract.py tests/test_shopping_secure_runtime.py
```

Both pytest runs use the reviewed fixture-only launcher: no ambient .env,
network, production configuration or generic subprocess execution. The only
child process allowed is the existing isolated read-port regression.

Preview commands:

```sh
.venv/bin/python -B scripts/preview_orange_coco.py --port 18080
python3 scripts/check_orange_coco_preview.py --origin http://127.0.0.1:18080
python3 scripts/check_orange_coco_preview.py --origin https://dev.bokstory.duckdns.org
```

The HTTP checker is strictly GET-only and accepts only the documented dev host
or loopback preview ports. The browser fixture runner was updated for the new
hero route/dimensions; its execution remains NOT_RUN.

## H. Remaining limitations

- 85 product photos still await consistent replacement. All exact paths remain
  in the current media manifest and all existing image routes remain valid.
- Browser layout, keyboard/accessibility, responsive crops and Back/Forward
  interaction are not executed browser tests. Source checks and direct image
  inspection do not imply Playwright PASS.
- Authenticated external dev verification was unavailable to this session;
  unauthenticated requests correctly encounter the existing 401 boundary.
- The local preview is a foreground development process with source reload,
  not a production deployment or launchd service. It was left running on 18080.
- Product details still expose only canonical fields; non-demo approved-image
  expansion and SHOP_RECOMMEND_001 remain deferred.

## I. Git and exact scope

Branch: `feature/homepage-product-management-console`; HEAD: `c4088a7`.
The original dirty tree is preserved. Index empty; no staging, commit or push.
The pre-existing dirty Caddyfile is byte-for-byte unchanged, SHA-256
`bd194de20fa51e59b619be1de2f8c0b730f89c17763316fabaec9308619aed73`.

Files changed in this finalization:

- `core/api/routes/homepage.py`
- `core/homepage/storefront.py`
- `core/homepage/preview.py` (new)
- `scripts/preview_orange_coco.py` (new)
- `scripts/check_orange_coco_preview.py` (new)
- `core/homepage/ui/storefront.html`
- `core/homepage/ui/storefront-search.html`
- `core/homepage/ui/storefront-product.html`
- `core/homepage/ui/storefront.css`
- `tests/test_shop_ui_001_storefront.py`
- `tests/test_shop_ui_002_storefront.py`
- `tests/test_shop_ui_002_preview.py` (new)
- `tests/shop_ui_001_fixtures.py`
- `tests/shop_ui_001_browser.cjs`
- `brands/orange-coco/assets/media/README.md` (new)
- `brands/orange-coco/assets/media/SHOP_MEDIA_001.json` (new)
- `brands/orange-coco/assets/media/storefront/hero-boutique.jpg` (new)
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/README.md`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/asset-manifest.json`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0001.jpg`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0002.jpg`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0003.jpg`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0004.jpg`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0008.jpg`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0012.jpg`
- `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/top/oc-demo-top-0016.jpg`
- `docs/architecture/SHOP-UI-002-DEMO-IMAGE-SWAP.md`
- `docs/architecture/SHOP-UI-002-EDITORIAL-HOME-SEARCH.md`
- `docs/architecture/SHOP-UI-002-STABILIZATION-SHOP-MEDIA-001.md` (new)
- `README.md`
- `CHANGELOG.md`
- `MASTER.md`
- `ROADMAP.md`
- `ARCHITECTURE.md`
