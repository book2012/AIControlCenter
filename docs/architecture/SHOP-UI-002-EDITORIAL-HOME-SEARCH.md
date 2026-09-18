# SHOP_UI_002 — editorial home, native navigation and discovery

**This navigation-stage record is superseded by the
[stabilization and SHOP_MEDIA_001 record](SHOP-UI-002-STABILIZATION-SHOP-MEDIA-001.md).**
That follow-up fixes the stale dev process, unifies preview/test composition,
adds the brand-owned hero and replaces seven product photos. Counts and runtime
statements below describe the earlier navigation-only pass.

Revision: 2026-09-14, navigation follow-up. Implementation only. This evolves
rather than resets the intentionally dirty SHOP_UI_001/002 tree and supersedes
the shell-only behavior in the [initial record](SHOP-UI-002-KOREAN-STOREFRONT.md).

## Architecture assessment

The defect was in the base presentation: HTML grids and most navigation entries
were empty until JavaScript fetched data and created links. Adding click
handlers alone could not satisfy native navigation. Homepage now renders
complete escaped HTML using the **same injected ShoppingService and canonical
response models** used by Shopping GET routes. It does not construct an adapter,
perform self-HTTP requests, or open a second commerce integration. Operator
pages keep their existing dependency boundary. No package was added.

`/homepage/storefront` stays a Korean editorial home: brand header, compact
140px mobile / 200px desktop photographic hero, short intro, category shortcuts,
four canonical NEW and four canonical BEST previews, and browse-all link.
No search/filter form, result count or pagination appears on home. Warm ivory
space, cocoa typography, orange accents and the 2/3/4 grid remain intact.

`/homepage/storefront/search` owns GET search, category selection, suggested
search terms, active conditions, counts and pagination. Every category anchor
uses `/homepage/storefront/search?category=<slug>` on home; all products uses
`/homepage/storefront/search`, NEW more uses `?category=new`, BEST more uses
`?category=best`. Canonical category slugs resolve to canonical IDs before
search reads, including numeric IDs from WooCommerce. Unknown slugs produce a
bounded empty listing, never an unfiltered catalog fallback. Filters on search
remain category and text query; no unsupported facets are invented.

Home and listing return actual product-card anchors in HTML. PDPs render on
`/homepage/storefront/product/{product_id}` and carry a validated `return_to`
URL. The HTML includes canonical name, exact price, availability, description,
approved local image and the purchase-unavailable notice. Valid demo PDPs return
200; unknown/invalid IDs return Korean 404 pages; unavailable reads return 503
with sanitized feedback and a retry control. Partial home failures preserve a
successful sibling section. Disabled Shopping never reaches its adapter.

Native GET forms, category/mood links, pagination and return links work without
scripts. Category/query/page state stays in URLs; page 1 is the implicit default.
Legacy filtered-home links redirect to search. JavaScript enhances subsequent
reads and history restoration without clearing the initial server render or
issuing duplicate initial home/PDP reads. Modified clicks retain native browser
behavior. AbortController, deadlines, version guards and lifecycle cancellation
remain in place. Browser execution of these enhancements is still NOT_RUN.

## Canonical reads and safety

| View | Canonical read semantics |
| --- | --- |
| Home | `/shopping/categories`, then one `/shopping/search` page of four for each returned `new`/`best` collection |
| Search | `/shopping/categories`, `/shopping/products` or composed `/shopping/search`; enhanced badges use one bounded page of at most 100 canonical members per NEW/BEST collection |
| PDP | `/shopping/products/{product_id}` only |

Initial HTML calls those existing service operations directly. Browser JSON
requests use only those canonical same-origin GET endpoints; PDP refresh/retry
has only the detail endpoint. No direct browser WooCommerce/WordPress API access,
commerce writes, persistent storage or service worker is introduced. Shopping
routes, schemas, adapters, catalog records and photo routes remain unchanged.
There is no HOT or featured/in-stock-first recommendation label. Recommendation
is deferred to SHOP_RECOMMEND_001. Product text is escaped server-side and uses
textContent client-side; prices never pass through binary float rendering.

## Image replacement summary

**0 / 92 binaries replaced.** The user-permitted local-plan fallback is used.
There is no complete product-matched replacement set in the workspace and no
browser crop QA in this environment. The [replacement plan](SHOP-UI-002-DEMO-IMAGE-SWAP.md)
and [92-entry exact-path manifest](SHOP-UI-002-DEMO-IMAGE-SWAP.json) record each
canonical product, current checksum, target JPEG, candidate path and route,
with a consistent adult international-fashion-model editorial brief. The
existing IDs, filenames, photo routing, provenance and bytes remain intact.
The manifest audit is part of the focused test suite. Actual sourcing/generation,
product matching, visual review, JPEG swaps and truthful provenance updates are
pending. The hero shares the top-0001 image and is included in that plan.

## Exact files changed in this follow-up

- `core/api/routes/homepage.py`
- `core/homepage/storefront.py` (new)
- `core/homepage/ui/storefront.html`
- `core/homepage/ui/storefront-search.html`
- `core/homepage/ui/storefront-product.html`
- `core/homepage/ui/storefront-card.html` (new)
- `core/homepage/ui/storefront.css`
- `core/homepage/ui/storefront.js`
- `tests/test_shop_ui_001_storefront.py`
- `tests/test_shop_ui_002_storefront.py`
- `tests/shop_ui_001_fixtures.py`
- `tests/shop_ui_001_browser.cjs`
- `docs/architecture/SHOP-UI-002-EDITORIAL-HOME-SEARCH.md`
- `docs/architecture/SHOP-UI-002-DEMO-IMAGE-SWAP.md` (new)
- `docs/architecture/SHOP-UI-002-DEMO-IMAGE-SWAP.json` (new)
- `README.md`
- `CHANGELOG.md`
- `MASTER.md`
- `ROADMAP.md`
- `ARCHITECTURE.md`

The pre-existing dirty `ops/macos/caddy/Caddyfile`,
`docs/architecture/SHOP-UI-002-KOREAN-STOREFRONT.md` and
`tests/shop_ui_002_helpers.js` were not edited in this follow-up.

## Known limitations and preview paths

Real browser layout, keyboard/accessibility, Back/Forward interaction and crop
QA remain unexecuted; static/source/helper tests do not count as Playwright.
SSR latency/availability follows the configured Shopping adapter. The server
and enhanced browser share formatting/state rules that require paired tests.
Only the approved demo photo mapping is displayed; non-demo photos keep the
existing fallback until a separate media approval policy is implemented.
Listing badges beyond the first 100 canonical members are not inferred.
Actual image replacement and recommendations remain deferred as above.

Preview paths on a separately started local development app:

- `/homepage/storefront`
- `/homepage/storefront/search`
- `/homepage/storefront/search?category=women-tops`
- `/homepage/storefront/search?category=new`
- `/homepage/storefront/search?category=best`
- `/homepage/storefront/product/oc-demo-top-0001`

These routes were verified through fixture TestClient requests, not a public
host. No preview server or production runtime was started or contacted.

## Exact validation

Focused source/API suite: **67 passed, 5 existing deprecation warnings in
0.85 seconds**, exit 0.

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_shop_ui_001_storefront.py tests/test_shop_ui_002_storefront.py
```

Relevant Homepage/Shopping regressions: **409 passed, 22 existing deprecation
warnings in 2.92 seconds**, exit 0.

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

Both commands reuse the reviewed fixture-only launcher: ambient configuration
and `.env` reads disabled, network blocked, bytecode/cache/plugin autoload
disabled, and only the existing guarded local port-isolation child permitted.

**40 JavaScriptCore helper checks passed**, exit 0:

```sh
/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc \
  tests/shop_ui_002_helpers.js
```

**2 JavaScript syntax checks passed**, exit 0, using JavaScriptCore
`new Function(readFile(...))` on `storefront.js` and the browser runner.

Offline fixture export: **592 canonical/static responses**, exit 0:

```sh
.venv/bin/python -B tests/shop_ui_001_fixtures.py /private/tmp/shop-ui-002-navigation.json
```

Playwright: **NOT_RUN**. Python Playwright is unavailable and Node is absent from
the shell PATH; no packages were installed. The existing offline browser suite
now covers native category, GET search, pagination, PDP and return links with
JavaScript disabled, plus normal enhanced navigation and canonical retry/failure
scenarios. HTML fixtures retain query-specific content and HTTP status codes. Actual browser layout/history/accessibility
verification and screenshots remain pending. Source/helper results are not
reported as browser passes.

`git diff --check`: PASS, with separate no-index whitespace checks for all
untracked source/test/documentation files. No files were staged for validation.

## Git and deployment boundary

The original dirty tree is preserved and evolved on
`feature/homepage-product-management-console`, HEAD `c4088a7`. The index remains
empty and HEAD unchanged. The pre-existing Caddyfile was not edited; its SHA-256
remains `bd194de20fa51e59b619be1de2f8c0b730f89c17763316fabaec9308619aed73`.
No production runtime, DNS, launchd, Ubuntu, current symlink, canonical Shopping
contract, or WooCommerce state was changed. No staging, commit, or push occurred.
