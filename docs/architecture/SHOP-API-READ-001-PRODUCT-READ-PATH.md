# SHOP_API_READ_001 — product list and detail

Status: source implementation complete; fixture validation passed; uncommitted.
This is the bounded source task authorized on 2026-09-12. Production activation
and live storefront validation remain separately governed work.

## Architecture and reuse

The existing path is retained:

`GET /shopping/products[/<id>] -> ShoppingService -> CommerceCatalogPort -> WooCommerceRESTAdapter -> WooCommerceReadTransportSession -> WooCommerce GET`.

Application composition still uses `ShoppingRuntime`, `get_shopping_service`,
the existing catalog factory, and the existing secure profile selector. No
configuration, credentials, service lifecycle, deployment target, or default
adapter was changed. Misconfigured WooCommerce selection still fails closed
through the existing factory; it does not fall back to a mock catalog.

AIControlCenter owns the `Product`, `ProductResponse`, and `ProductListResponse`
contracts, query checks, response validation, deterministic JSON, and error
surface. WooCommerce remains the catalog/Commerce Engine. Its field mapping
stays inside the existing replaceable `WooCommerceRESTAdapter`; vendor metadata,
links, and unknown fields never become public product fields. The adapter reuses
the existing external-read policy and bounded GET transport. It exposes no new
write method. The Mac mini remains the sole Control Plane.

`CommerceCatalogPort` is the existing synchronous public catalog seam. The
separate asynchronous `CommerceReadPort`, `ProductSnapshot` schemas, normalizer,
and snapshot-envelope contracts are preserved. This change neither creates a
second API nor relabels the current storefront contract as `/shopping/v1`.
Existing string product IDs retain their public compatibility semantics; no new
canonical snapshot identity scheme is introduced.

## API and canonical JSON

| Operation | Input | Success |
| --- | --- | --- |
| `GET /shopping/products` | `page=1`, `page_size=20`; page >= 1, size 1–100 | `{items, total, page, page_size}` |
| `GET /shopping/products/{product_id}` | Existing string ID; WooCommerce accepts positive ASCII decimal IDs of at most 20 digits without leading zeros | One product |

Both routes keep their existing response models. Product fields are exactly
`id`, `name`, `slug`, `description`, `price`, `currency`, `category`, `in_stock`,
`source`, and `image_url`. The service returns JSON-compatible dictionaries;
HTTP success responses use UTF-8, sorted object keys, compact separators, and
reject non-finite numbers. No clock, random ID, or observation timestamp is
inserted. Identical observations produce identical response bytes.

Example detail response:

```json
{"category":"Shirts","currency":"KRW","description":"<p>Cotton</p>","id":"42","image_url":"https://images.example.test/shirt.jpg","in_stock":true,"name":"코튼 셔츠","price":"25000","slug":"cotton-shirt","source":"woocommerce"}
```

Money remains a decimal **string**, never a binary float. The WooCommerce
adapter normalizes equivalent values such as `25000.00` and `25000` without
decimal-context rounding. The existing WooCommerce catalog currency is **KRW**;
this task adds no currency discovery or multi-currency support. An explicit
conflicting payload currency is rejected. Missing, malformed, negative, or
non-finite prices fail closed instead of becoming a synthetic zero.

The existing presentation projection uses the first category and first image;
missing optional collections yield `Uncategorized` and `null`. Absent slug and
description yield empty strings; supplied HTML descriptions remain strings.
`instock` maps to true, `outofstock` and `onbackorder` to false; unknown stock
states fail closed. Only explicitly published products are exposed. Recognized
nonpublic detail products return not found; missing/unknown visibility is an
invalid observation.

## Adapter and failure contract

Product list and detail methods reuse `list_products_raw` and `get_product_raw`.
Before I/O they validate queries and evaluate the existing GET allowlist.
Lists request `context=view`, `status=publish`, `orderby=id`, `order=asc`,
`page`, and `per_page`. Details request `context=view` on the validated numeric
resource. Detail identity must match the requested ID.

Lists require a valid `X-WP-Total`, matching page cardinality, and unique ascending
numeric IDs. Empty catalogs and successful empty pages beyond the total are
valid. Inconsistent observations fail closed; page-number pagination does not
promise a transactionally frozen catalog across concurrent upstream changes.

The reused transport makes one GET attempt with bounded connect/read timeouts
and its existing total-deadline check. Redirect following and retries are
disabled; session initialization clears proxies, existing cookies, and response
hooks, and environment proxy inheritance is disabled. Non-200 responses are
rejected; an actual detail HTTP 404 alone maps to an absent upstream product.
No upstream error body, request credential, or authentication header is returned.

| Condition | Public result |
| --- | --- |
| Absent or recognized nonpublic product | 404, `shopping_product_not_found` and requested ID |
| Invalid ID or direct service pagination | 422, `shopping_invalid_product_query` |
| FastAPI query type/range failure | Existing FastAPI 422 validation response |
| Disabled catalog, policy denial, transport/status/JSON/mapping/page failure | 503, `shopping_catalog_unavailable` |
| POST / PUT / PATCH / DELETE on either product route | 405; no adapter invocation |

`CatalogReadQueryError` and `CatalogReadUnavailable` belong to the catalog port.
`WooCommerceAPIError` implements the latter without making routes import the
vendor. Successful empty results remain distinct from unavailable results.
No persistence, caching, fallback products, write authority, or automatic retry
was added. Existing search, category, featured, and dashboard APIs retain their
surfaces; their shared transport/mapping dependencies were regression tested.

## Exact validation

Final focused run: **113 passed, 1 deprecation warning**.

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_shop_api_read_001.py \
  tests/test_woocommerce_adapter.py \
  tests/test_shopping_woocommerce_normalization.py \
  tests/test_shopping_woocommerce_read_transport.py
```

Final shopping regression: **166 passed, 15 deprecation warnings**.

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_shopping_api.py \
  tests/test_shopping_catalog.py \
  tests/test_shopping_categories.py \
  tests/test_shopping_featured.py \
  tests/test_shopping_search.py \
  tests/test_shopping_factory.py \
  tests/test_shopping_settings.py \
  tests/test_shopping_secure_runtime.py \
  tests/test_shopping_management_source.py \
  tests/test_shopping_management_read_model.py \
  tests/test_dashboard_shopping_management.py \
  tests/test_homepage_shopping_dashboard_contracts.py \
  tests/test_shopping_adapter_contract_isolation.py \
  tests/test_shopping_commerce_adapter_contract.py \
  tests/test_shopping_woocommerce_commerce_read.py \
  tests/test_shopping_read_only_ports.py \
  tests/test_shopping_external_read_policy.py \
  tests/test_shopping_schema_contracts.py \
  tests/test_shopping_demo_adapter.py \
  tests/test_product_draft_read_queries.py \
  tests/test_shopping_health_failure_compatibility.py \
  tests/test_shopping_read_authorization.py
```

The session-only launcher clears ambient application environment, replaces
`ConfigLoader.load` before application import to prevent `.env` reads, disables
pytest plugin autoload/cache and bytecode output, uses an isolated temporary
fixture root, and blocks socket connections and subprocesses. Its sole process
exception is the exact existing port-isolation test's local Python program,
which installs its own side-effect guards. Secure-runtime tests use temporary
fake credential files only. The launcher is not a product/runtime component.
The new suite also constructs a minimal FastAPI app with an injected catalog,
so it requires neither the application bootstrap nor any credential provider.

The first regression run blocked that local isolation child; the harness was
corrected and the full selected regression rerun passed. No application test
was skipped or weakened. Final evidence above follows the last source edit.

## Closure boundary

Git baseline: clean `feature/homepage-product-management-console`, HEAD
`c1a88dd`. Source work and all six documentation files remain uncommitted.
There is no implementation blocker. Runtime activation and live verification
are not authorized by this task. No production or Ubuntu access, launchctl,
real credential access, external write, staging, commit, or push was performed.
