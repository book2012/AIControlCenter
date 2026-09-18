# SHOP_UI_002 — Korean canonical storefront and product preview

Current revision: [2026-09-14 editorial home / search split](SHOP-UI-002-EDITORIAL-HOME-SEARCH.md).
The record below describes the earlier 2026-09-13 implementation and its validation.

Implementation only, 2026-09-13. No staging, commit, push, installation, or runtime
activation. Source tests passed; Playwright interaction/visual checks are NOT_RUN.

## A. Architecture assessment

The existing dirty SHOP_UI_001 storefront is evolved in place. Its FastAPI
asset-serving seam, local approved-photo route, GET request wrapper, timeout,
cancellation, stale-response checks, and exact decimal approach are retained.
The visible user requirements supply the redesign specification; a separate
SHOP_UX_REDESIGN_001 analysis artifact was not found in the repository.

The new `/homepage/storefront/product/{product_id}` route serves a separate HTML
shell. It does not load the Shopping runtime or inject untrusted path values
into HTML. Its JavaScript reads the canonical detail endpoint and verifies the
returned identity. Missing/nonpublic products show a Korean not-found state;
transport, timeout, malformed JSON, and identity/schema failures show unavailable
states with explicit retry. The HTML shell itself returns HTTP 200; canonical
product absence is HTTP 404 from the data API and is rendered client-side.

AIControlCenter retains business logic and contract ownership on the Mac mini.
WordPress/WooCommerce remain CMS/Commerce engines. No Shopping schema, service,
adapter, factory, or runtime-composition change was needed. WooCommerce search
expects category IDs; controls now take IDs from the canonical category API
instead of assuming demo aliases such as `top` work for every adapter.

## B. Files changed

Source:

- `core/api/routes/homepage.py`: additive product-preview shell route on top of
  the existing uncommitted storefront routes.
- `core/homepage/ui/storefront.html`: Korean catalog shell and search/category
  composition; existing hero photo retained.
- `core/homepage/ui/storefront-product.html`: new separate preview shell.
- `core/homepage/ui/storefront.css`: warm palette, compact hero, accessible
  controls, responsive listing, and preview layouts.
- `core/homepage/ui/storefront.js`: canonical reads, real links, URL/history
  state, detail rendering, category IDs, and source membership badges.

Tests and evidence:

- `tests/test_shop_ui_001_storefront.py`: retained/evolved route, photo, and safety
  contracts for the original dirty implementation.
- `tests/test_shop_ui_002_storefront.py`: Korean, detail, URL architecture,
  canonical read, category/search, and no-write source/API tests.
- `tests/shop_ui_001_fixtures.py`: expanded offline fixture export, retaining its
  existing runner path.
- `tests/shop_ui_001_browser.cjs`: evolved offline browser suite for SHOP_UI_002.
- `tests/shop_ui_002_helpers.js`: pure helper checks using system JavaScriptCore.
- README, CHANGELOG, MASTER, ROADMAP, ARCHITECTURE, and this assessment.

## C. User-visible changes

Both shells use `lang=ko` and Korean navigation/status/error copy. Pastel orange,
warm ivory, and cocoa replace the stronger orange/English editorial treatment.
The hero uses the existing photo in a compact side-by-side layout, including
mobile. Product grids retain two mobile, three tablet, and four desktop columns.
Focusable product-card links support keyboard and ordinary browser navigation.

Search is visible beside the category controls. Category selection preserves
the search term; submitting a search preserves the category. Either action
resets pagination to one. Mood buttons submit suggested Korean searches within
the current category, and the UI explicitly says they are not product facets.
NEW/BEST labels require canonical source membership; no HOT promotion is shown.
Cart, social-placeholder, and wishlist controls are removed.

The preview displays canonical name, exact price/currency, availability,
description, and the existing approved image when available. It states:

> 상품 미리보기 · 현재 구매는 지원하지 않습니다.

There are no invented gallery, size, color, material, fit, variant, or commercial
actions. No product photo file was modified or replaced.

## D. Canonical APIs consumed

| View/use | GET endpoint |
| --- | --- |
| Unfiltered listing | `/shopping/products?page={page}&page_size=12` |
| Category/query combination | `/shopping/search?category={canonical_id}&q={query}&page={page}&page_size=12` (only active filters included) |
| Category controls | `/shopping/categories` |
| NEW/BEST membership | `/shopping/search?category={canonical_collection_id}&page=1&page_size=100`, only for returned canonical `new`/`best` slugs |
| Product preview data | `/shopping/products/{product_id}` only |

Local Homepage CSS/JS and the existing allowlisted repository JPEG route are
presentation assets, not additional data APIs. The browser never contacts
WooCommerce/WordPress APIs, a CMS host, or unapproved media origins. All data
reads pass a same-origin canonical-path allowlist with GET and redirect refusal.

The listing URL stores `category`, `q`, and `page`. Push/replace history and
popstate handlers restore these controls/results. Product links include an
encoded `return_to` listing URL; only the exact local listing pathname and
known filter parameters survive validation. Page lifecycle handlers cancel
reads on departure and reload on a persisted browser-page restoration. No
local/session storage, cookies, IndexedDB, persistent wishlist, or cache is used.

## E. Exact validation

Final selected Python source/API regressions: **451 passed, 22 existing
deprecation warnings in 3.38 seconds**, exit 0.

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_shop_ui_001_storefront.py tests/test_shop_ui_002_storefront.py \
  tests/test_homepage_api.py tests/test_ui_01_homepage.py \
  tests/test_homepage_projection.py tests/test_homepage_status.py \
  tests/test_homepage_shopping_dashboard_contracts.py \
  tests/test_shopping_api.py tests/test_shopping_catalog.py \
  tests/test_shopping_categories.py tests/test_shopping_featured.py \
  tests/test_shopping_search.py tests/test_shopping_demo_adapter.py \
  tests/test_shop_api_read_001.py tests/test_shop_api_read_002.py \
  tests/test_shop_api_read_003.py tests/test_woocommerce_adapter.py \
  tests/test_shopping_woocommerce_normalization.py \
  tests/test_shopping_woocommerce_read_transport.py \
  tests/test_shopping_factory.py tests/test_shopping_read_only_ports.py \
  tests/test_shopping_external_read_policy.py \
  tests/test_dashboard_shopping_management.py \
  tests/test_shopping_management_read_model.py \
  tests/test_shopping_adapter_contract_isolation.py \
  tests/test_shopping_commerce_adapter_contract.py \
  tests/test_shopping_secure_runtime.py
```

The reviewed session launcher disables ambient application config and `.env`
loading, pytest plugin autoload/cache, and bytecode writes. It blocks network
connections and subprocesses except the existing guarded local port-isolation
test child. Tests use injected fixture services and fake credentials.

System JavaScriptCore: **31 helper checks passed**, exit 0, for exact decimal
digits/trailing zeroes, product validation, hostile text preservation, and page
validation. The test exposes pure functions before the IIFE browser bootstrap;
it does not simulate or claim DOM/history behavior.

```sh
/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc \
  tests/shop_ui_002_helpers.js
```

**2 JavaScript syntax checks passed**, exit 0: `storefront.js` and the offline
browser runner, parsed with JavaScriptCore `new Function(readFile(...))`.

Offline fixture export: **227 canonical/static responses exported**, exit 0.

```sh
.venv/bin/python -B tests/shop_ui_001_fixtures.py /private/tmp/shop-ui-002.json
```

Playwright: **NOT_RUN**. Python Playwright is absent, Node is unavailable on the
shell PATH, and the provided JavaScript runtime could not load Playwright. No
packages were installed. The updated offline suite covers Korean views,
responsive layout, keyboard navigation, category/query/page history, PDP return
URLs, valid/not-found/error/timeout states, stale responses, exact prices,
untrusted content, canonical requests, and storage absence. Its assertions and
screenshots are pending execution; no browser PASS is claimed.

`git diff --check`: PASS. The same check is also applied separately to new
untracked source/test files so whitespace review does not depend on staging.

## F. Deferred items

Browser interaction, visual, and accessibility QA using the prepared offline
suite remains pending. Product attributes absent from canonical contracts,
commerce actions, persistent wishlists, photo replacement, new media approval,
API feature expansion, production activation, and Git closure are outside scope.

## G. Known limitations

- A usable browser/Playwright run has not verified Back/Forward, responsive
  geometry, focus behavior, or screenshots. Source/API/helper passes are distinct
  from browser verification.
- Product descriptions are rendered with `textContent`; supplied HTML is shown
  as literal text, not executed or interpreted as rich content.
- Only SHOP_UI_001's existing approved repository demo JPEG mapping is retained.
  Unapproved/remote WooCommerce images show a Korean image-unavailable message.
- Badge reads cover at most 100 products per canonical collection. Products
  beyond that bounded observation receive no inferred badge.
- Suggested Korean searches can legitimately return no results, depending on
  the canonical source's text. No synthetic facet or fallback result is added.
- Product previews require JavaScript for product data; HTML shells themselves
  are not server-rendered product/404 pages. Scroll restoration uses browser
  behavior rather than persistent custom state.

## H. Git and authority boundary

Baseline: `feature/homepage-product-management-console`, HEAD `c4088a7`.
Existing dirty files included Homepage routes, three storefront assets, three
SHOP_UI_001 test files, and `ops/macos/caddy/Caddyfile`. All were preserved or
evolved within scope; the Caddyfile was not edited. Its before/after SHA-256 is
`bd194de20fa51e59b619be1de2f8c0b730f89c17763316fabaec9308619aed73`.

The index remains empty and HEAD unchanged. Task changes are deliberately
unstaged/uncommitted alongside the preserved original work. No Caddy/DNS,
launchd/runtime, production-current symlink, Ubuntu, production data, or
WooCommerce state was accessed or changed. No package install, staging, commit,
or push occurred. This implementation grants no activation authority.
