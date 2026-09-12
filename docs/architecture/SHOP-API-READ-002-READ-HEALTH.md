# SHOP_API_READ_002 — read-path health and failure observability

Status: source implementation complete; fixture validation passed (2026-09-13).
Baseline: clean approved `feature/homepage-product-management-console`,
HEAD `6cae4c1`, synchronized with its configured upstream. Source and Git work
are within the repository workflow; live reads and runtime activation are not
authorized by this task.

## Read-path health

`GET /shopping/health/read-path` invokes
`ShoppingService.list_products(page=1, page_size=1)`. It exercises the configured
catalog through the existing factory/composition, catalog port, WooCommerce
adapter, external-read policy, and bounded GET transport. The service does not
inspect vendor exceptions or select a different adapter for the probe.

The WooCommerce request uses `context=view`, `status=publish`, `page=1`,
`per_page=1`, `orderby=id`, and `order=asc`. One authorized request is made;
disabled catalogs and policy denials make none. No retry, redirect following,
cached success, fallback catalog, scheduler, or write method was added.
`WooCommerceRESTAdapter.health()` also uses this validated adapter list path.

HTTP 200 is insufficient: JSON, collection shape, `X-WP-Total`, cardinality,
identity/order, visibility, fields, monetary values, and UTF-8 renderability
must pass the existing read contract and new service validation. An empty
catalog with total zero is healthy. A failure never becomes an empty success.

Healthy response (HTTP 200):

```json
{"failure_code":"none","healthy":true,"read_only":true,"service":"AIShoppingPlatform","state":"HEALTHY"}
```

Malformed JSON response (HTTP 503):

```json
{"failure_code":"invalid_payload","healthy":false,"read_only":true,"service":"AIShoppingPlatform","state":"UNAVAILABLE"}
```

Existing `/shopping/health` and `/shopping/readiness` remain configuration-only
and do not perform an external read. The new probe validates one sampled list
page; it is not an exhaustive catalog audit or a guarantee about every detail
resource. Each explicit probe is fresh, and a later observation may differ.
No endpoint was called against a live runtime during this task.

## Failure classification and observability

`CatalogReadUnavailable.failure_code` carries the existing repository-owned
`HealthFailureCode` enum across the catalog boundary. `WooCommerceAPIError`
retains its inheritance and `status_code` compatibility. Classification is
assigned where the failure is detected; it does not parse exception text.

| Observation | Failure code | Health state |
| --- | --- | --- |
| Valid product page, including empty catalog | `none` | `HEALTHY` |
| Requests timeout, including existing total-deadline failure | `timeout` | `UNAVAILABLE` |
| Connection or other Requests transport failure | `transport` | `UNAVAILABLE` |
| HTTP 401 | `authentication` | `UNAVAILABLE` |
| HTTP 403 or local read-policy denial | `authorization` | `UNAVAILABLE` |
| HTTP 429 | `rate_limit` | `DEGRADED` |
| Other non-200 status, including collection HTTP 404 and redirects | `dependency_unavailable` | `UNAVAILABLE` |
| JSON decoder failure | `invalid_payload` | `UNAVAILABLE` |
| Invalid product/page/visibility/money/Unicode or service projection | `schema_mismatch` | `UNAVAILABLE` |
| Disabled catalog or invalid adapter identity configuration | `configuration` | `UNAVAILABLE` |
| Unexpected adapter exception or unrecognized failure code | `unknown` | `UNAVAILABLE` |

All failed health responses use HTTP 503 and `healthy=false`, including rate
limiting. State mapping reuses `DEFAULT_STATE_BY_FAILURE`; existing health
normalization and aggregation contracts are unchanged. Invalid codes and
success-only codes supplied to an unavailable exception normalize to `unknown`.
Factory failures before service composition retain the existing fail-closed
behavior; the health route does not bypass failed runtime composition.

Malformed upstream responses are observable through typed adapter failures and
the explicit read-health projection. Neither surface includes raw upstream
bodies or request credentials. Unexpected adapter exceptions are sanitized at
the service boundary. No logging of exception text, stack traces, URLs,
authentication headers, product payloads, or query values was added.

The observability package currently contains pure health contracts (including
an optional latency field), not an active request logger, counter collector,
or exporter. Latency and cumulative request-outcome instrumentation are deferred
under the task's conditional requirement. No new sink or persistence convention
is introduced. No wall-clock time, latency, or random identifier is inserted
into deterministic public JSON.

## Deterministic product errors and compatibility

Product list/detail success shapes remain those of SHOP_API_READ_001. The same
sorted-key, compact, UTF-8 renderer now renders product errors and read health.

| Product read result | HTTP | Body |
| --- | --- | --- |
| Invalid identifier or pagination | 422 | `{"detail":{"code":"shopping_invalid_product_query"}}` |
| Catalog unavailable | 503 | `{"detail":{"code":"shopping_catalog_unavailable"}}` |
| Absent/nonpublic detail product | 404 | `{"detail":{"code":"shopping_product_not_found","product_id":"42"}}` |

Framework product-query type/range errors intentionally change from FastAPI's
validation-detail list to the existing service query-error code. This removes
input echo and stabilizes error bytes. Other shopping routes retain their
framework validation contract. OpenAPI documents product 404/422/503 error
models and read-health 200/503 models. Only an actual detail HTTP 404 maps to
upstream absence; collection 404 remains unavailable.

Service projection additionally rejects invalid replacement-catalog result
shapes, non-integer totals, inconsistent page cardinality, non-Product objects,
and strings containing unpaired surrogates. These failures return sanitized
503 responses instead of escaping as attribute or encoding exceptions.

POST, PUT, PATCH, and DELETE remain HTTP 405 on product and read-health paths,
without adapter invocation. The existing transport still makes at most one
bounded GET with redirects and retries disabled and credentials scrubbed.

## Validation evidence

Final combined fixture run after the last source change:
**413 passed, 15 existing deprecation warnings in 1.82 seconds**, exit 0.

```sh
.venv/bin/python /private/tmp/shop_api_read_001_tests.py -q \
  tests/test_shop_api_read_002.py \
  tests/test_shop_api_read_001.py \
  tests/test_woocommerce_adapter.py \
  tests/test_shopping_woocommerce_normalization.py \
  tests/test_shopping_woocommerce_read_transport.py \
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
  tests/test_shopping_read_authorization.py \
  tests/test_shopping_adapter_health_probe.py \
  tests/test_shopping_health_monitor.py
```

The reviewed session-only launcher is reused from SHOP_API_READ_001. It clears
ambient application environment, disables `.env` loading before application
import, blocks socket connections and subprocesses, disables bytecode/plugin
autoload/pytest cache, and uses a temporary fixture directory. Its only process
exception is the existing local port-isolation test program with its own
side-effect guards. Secure-runtime tests use temporary fake credentials. The
launcher is not a runtime component or committed artifact.

An earlier regression run found the route-inventory contract needed updating
for the new health route. Product routes now register directly with a scoped
route-class override, and the exact GET-only inventory includes read health.
The full selected regression passed after correction; no failing test was
skipped or weakened. This is bounded fixture evidence, not a full repository
deployment regression or a live storefront health claim.

## Authority boundary

The Mac mini remains the sole Brain/Control Plane, and AIControlCenter owns
policy, orchestration, contracts, health/error projections, and authorization.
WordPress remains the CMS Engine and WooCommerce the Commerce Engine. Ubuntu,
Caddy, deployment configuration, DPL, and runtime lifecycle are outside scope.
No production/Ubuntu access, real credential reads, production mutation,
WooCommerce state change, or activation occurred. Feature-branch source commit
and push do not authorize runtime activation.
