# SHOP_API_READ_003 — bounded operational telemetry and Dashboard consumption

Status: source implementation complete; fixture validation passed (2026-09-13).
Implementation commit: `9bc8890`, committed and pushed on
`feature/homepage-product-management-console`. Documentation closeout started
with a clean working tree at that HEAD and local HEAD/upstream comparison `0 0`.
This sprint supersedes the telemetry deferral recorded in SHOP_API_READ_002.

## Architecture

The canonical path remains `ShoppingService -> CommerceCatalogPort ->
WooCommerceRESTAdapter -> external-read policy / bounded GET transport`.
The existing application-owned `ShoppingRuntime.catalog_service` now owns one
`CatalogReadTelemetry` instance. It observes the service's public list, detail,
and explicit read-health operations, including service validation, configured
read denials, adapter execution, and product projection. The existing factory,
secure profile selection, vendor mapping, GET policy, and transport are unchanged.

List and read-health use the same internal list implementation. The explicit
probe has its own observation slot and records once, without also incrementing
the public list slot. It still makes at most one upstream GET, and no upstream
request on configuration/policy denial. Product and read-health response bodies
retain SHOP_API_READ_001/002 compatibility, including deterministic JSON bytes.
Configuration-only liveness and readiness retain their existing behavior.

The Mac mini M4 remains the always-on Brain and sole Control Plane.
AIControlCenter owns orchestration, authorization, business logic, telemetry,
and Dashboard projections. WordPress remains the CMS Engine; WooCommerce remains
the Commerce Engine. The new code does not depend on a vendor-specific adapter.

## Telemetry contract

`ShoppingService.read_path_telemetry()` returns an immutable
`CatalogReadTelemetrySnapshot`; `to_json()` returns detached JSON data. Snapshot
reads do not perform I/O, sample a clock, or increment counters.

The snapshot contains `scope=service_instance`,
`observation_basis=last_completed_read_per_operation`, `total`, `operations`,
and `health`. There are exactly three operation slots: `list_products`,
`get_product`, and `read_path_health`. Each contains `total`, fixed `outcomes`
and `failures` counters, and `last={outcome, probe}` (initially `null`).

| Completed service invocation | Outcome | Health evidence |
| --- | --- | --- |
| Valid product or page, including valid empty catalog/page | `success` | `none`, `HEALTHY` |
| Absent or recognized nonpublic detail product | `not_found` | `none`, `HEALTHY` |
| Invalid service query or adapter ID rejection | `invalid_query` | `probe=null`; no new dependency evidence |
| Disabled catalog, policy denial, or read/projection failure | `unavailable` | Existing classified failure and mapped state |
| Adapter rejects the fixed valid read-health query | `unavailable` | `unknown`, `UNAVAILABLE` |
| Unavailable observation supplied with `failure=None` | `unavailable` | Normalized to `unknown`, `UNAVAILABLE` |

Failure counters use the existing `HealthFailureCode` vocabulary: `timeout`,
`transport`, `authentication`, `authorization`, `rate_limit`, `invalid_payload`,
`schema_mismatch`, `dependency_unavailable`, `configuration`, and `unknown`.
Only unavailable outcomes increment failure counters. Success code `none` and
threshold code `latency` are excluded; this sprint defines no latency threshold.
An unavailable outcome with `failure=None` normalizes to `HealthFailureCode.UNKNOWN`
before probe creation or counter publication, preserving the complete observation.
No query, product ID, URL, credential, provider payload, or exception text is a
counter label or observation field.

`probe` is the existing `HealthProbeResult.to_json()` contract, constructed by
`normalize_adapter_health`. It contains the existing `AdapterHealth` contract
with logical adapter name `catalog`, UTC `checked_at`, nonnegative integer or
null `latency_ms`, canonical status, and `message=null`. `detail_code` is a
repository-owned `shopping.catalog.read.<outcome>` code. There is no second
health enum, failure map, or adapter-health schema.

Latency measures elapsed service execution through validated projection, using
an injectable monotonic nanosecond clock and integer truncation to milliseconds.
It excludes telemetry publication and HTTP rendering. Unavailable or backwards
clock readings produce `latency_ms=null`; they never fabricate zero latency.
Query rejections have no health probe or published latency. The injectable UTC
clock supplies only the canonical observation timestamp, never the duration.
Identical operation order, fixture results, and clock inputs produce identical
telemetry. Polling an unchanged snapshot produces identical telemetry bytes.
Operational timestamps and timings are confined to telemetry; existing public
product and read-health JSON does not acquire them.

The aggregate is the existing `HealthMonitorSnapshot` from `aggregate_health`.
Its `adapters` map is keyed by the three operation names, so its counts describe
observed operation slots, not distinct vendors. It retains the latest health
evidence per operation; query rejection cannot erase previous health evidence.
No observations means `empty=true`, counts zero, and `UNAVAILABLE`, without
claiming an upstream failure. State precedence remains
`UNAVAILABLE > DEGRADED > HEALTHY`; rate limiting remains degraded. Recovery
replaces the affected slot's health while cumulative failure counts remain.

This is last-observed health, not a fresh probe, freshness guarantee, catalog
audit, SLO, or production readiness decision. Unobserved operations are absent
from the health aggregate. Each observation retains its original `checked_at`;
there is no TTL or polling job. Counts describe completed service invocations,
not HTTP requests or outbound attempts. FastAPI rejections before service
invocation, unsupported HTTP methods, direct adapter calls, search, categories,
and featured reads are outside this bounded metric scope. Dashboard management
list reads already using this service are included.

There was no active generic request collector to reuse. The new bounded
bookkeeping reuses the Shopping health/latency contracts; unrelated governance
job metrics and their persistence remain untouched. Each service instance keeps
fixed counter keys plus the last outcome and last health evidence for three
operations. No event list or product data is retained. Publication and snapshot
copying use a lock, never held over adapter I/O. Concurrent publication order
defines the latest observation. Instances do not share counters; restarting or
replacing the service resets them. There is no persistence or cross-process
aggregation. Telemetry publication failures are best effort and cannot replace
a catalog success or error; such failures can omit an observation, so counters
are operational observations rather than an audit ledger.

## Dashboard surface

`DashboardAPI` accepts an optional callable returning the typed snapshot and
adds `shopping_read_telemetry` using the existing optional-projection and
failure-isolation conventions. The normal `GET /dashboard` composition supplies
the same application-owned service. Existing management collection happens
first, so its list observation is included without another catalog request.
Other existing Dashboard sources retain their behavior.

`GET /dashboard/shopping/read-telemetry` returns only this projection, without
collecting management products, workers, datacenter, or governance sources.
Its schema is `{schema_version: "1.0", mode: "READ_ONLY", status, telemetry,
error}`. `status` is the aggregate's observed health state. An empty available
collector returns its zero snapshot and `error=null`; a projection exception
returns `telemetry=null`, `status=UNAVAILABLE`, and the sanitized code
`SHOPPING_READ_TELEMETRY_UNAVAILABLE`. Both are HTTP 200 projection responses;
they are distinct from the explicit live read-health route's HTTP 200/503.
POST, PUT, PATCH, and DELETE return 405 without service invocation.

The Dashboard imports AIControlCenter Python models and services only. It has
no new vendor dependency or network client. No frontend bundle, exporter,
notification, or background integration is part of this sprint.

## Exact validation

Final combined fixture run after the last source/test edit, with the same 34
test files and one added focused case:
**488 passed, 22 existing deprecation warnings in 3.05 seconds**, exit 0.

```sh
.venv/bin/python -B tests/run_shop_api_read_regression.py -q --tb=short \
  tests/test_shop_api_read_003.py \
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
  tests/test_shopping_health_monitor.py \
  tests/test_shop_01d_dashboard_closeout.py \
  tests/test_shop_02d_api_dashboard.py \
  tests/test_dashboard_api_integrated.py \
  tests/test_monitoring_snapshot_health_adapter.py
git diff --check
git status --short
```

Before the telemetry hardening, the same command reproduced the original
bounded scope through repository-owned tooling: **487 passed, 22 warnings in
3.10 seconds**, exit 0. The new focused test first reproduced the incomplete
observation's `AttributeError` at `failure.value`: **1 failed, 1 warning in
0.26 seconds**, exit 1. After the two-line normalization, the same focused command
passed: **1 passed, 1 warning in 0.24 seconds**, exit 0:

```sh
.venv/bin/python -B tests/run_shop_api_read_regression.py -q --tb=short \
  tests/test_shop_api_read_003.py::test_unavailable_without_failure_records_unknown_observation
```

The final 22 warnings are unchanged: 20 `datetime.utcnow()` deprecations
(8 reported at `<string>:9` and 12 from `core/brain/status.py`),
1 Starlette TestClient/httpx deprecation, and 1 HTTP 422 constant deprecation.
There are no failures, errors, skipped tests, or deselections in the final run.

The repository-owned `tests/run_shop_api_read_regression.py` uses the existing
`pytest.ini` and reproduces the former session-only launcher's fixture guards. It
clears ambient application configuration, disables `.env` loading before app
import, blocks socket connections and subprocesses, disables pytest plugins,
cache, and bytecode, and uses temporary fixture storage. Its only subprocess
exception is the reviewed local port-isolation test with its own side-effect
guards. Fake credentials, HTTP responses, clocks, services, and Dashboard
dependencies are used; the concurrency test uses a local in-memory catalog.
The repository root is derived from the launcher's file location; no temporary
launcher or workstation-specific checkout path is required. Temporary paths
hold disposable fixture storage only. This is test tooling, not a runtime component.

The new suite covers classification across all three operations, canonical
AdapterHealth schema validation, one observation per probe, empty/not-found
semantics, recovery, denial without I/O, invalid-query boundaries, deterministic
clocks/JSON, detached snapshots, 240 concurrent fixture reads, per-instance
reset, telemetry and Dashboard failure isolation, runtime service sharing,
absence of extra catalog reads, GET-only routes, and dependency isolation.
The added focused case proves a missing unavailable failure code still publishes
one total, one unavailable outcome, one `unknown` failure, the last probe, and
one unavailable health observation.
Earlier runs found a test registry-name typo, a not-found telemetry failure-code
bug, and the existing Dashboard route-inventory expectation. All were corrected
before the final complete selected run; no failing test was skipped or weakened.

## Closure and authority

ARCHITECTURE.md, README.md, CHANGELOG.md, MASTER.md, ROADMAP.md, and this record
were updated only after green fixture regressions. No production or Ubuntu
access, Production Runtime access, launchctl, runtime activation, production
write, WooCommerce mutation, persistence, background job, exporter, or new
write authority was introduced or exercised. Host Caddy and deployment remain
outside scope. Production activation remains not authorized and was not performed.

The implementation was committed and pushed as `9bc8890`, with a clean post-push
working tree and local HEAD/upstream comparison `0 0`. This documentation-only
reconciliation changes only the six files named above; application code, tests,
and the index are unchanged. `git diff --check` passes, HEAD remains `9bc8890`,
and local HEAD/upstream comparison remains `0 0`.

`SHOP_API_READ_003_IMPLEMENTATION=COMPLETE`
`SHOP_API_READ_003_VALIDATION=FIXTURE_ONLY_PASS`
`SHOP_API_READ_003_IMPLEMENTATION_COMMIT=9bc8890`
`SHOP_API_READ_003_GIT=COMMITTED_AND_PUSHED`
`SHOP_API_READ_003_PRODUCTION_ACTIVATION=NOT_AUTHORIZED`

Blockers: none for this bounded source sprint. Live validation and activation
remain separate unauthorized work. Implementation commit `9bc8890`:
`feat(shopping): add bounded read telemetry and dashboard projection`
