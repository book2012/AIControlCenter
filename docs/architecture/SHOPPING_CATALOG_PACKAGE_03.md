# Shopping catalog package extraction — 0.3.0

Date: 2026-11-03 (Asia/Seoul)
Status: catalog implementation extraction and isolated validation complete.
No production activation or live provider connection.

## Plugin-owned implementation
- catalog_service.py: product list/detail/search, featured products, categories,
  canonical payload validation, read-path health and bounded read telemetry.
- catalog_ports.py: catalog read contract and fixed failure types.
- catalog_settings.py: immutable public configuration projection; no provider URL,
  consumer key, secret reference, secret value or environment loader.
- adapters/mock_commerce.py: existing five synthetic sample products and reads.
- schemas.py: existing Pydantic response models, including variants.
- observability/{health_probe,health_monitor,read_telemetry}.py: catalog read status,
  aggregation and instance-local observation. No polling, persistence or jobs.
- contracts/provisional.py: existing pure JSON type aliases, not policy execution.
- Product/order domain remains in this wheel from version 0.2.0.

Public API: construct the plugin ShoppingService with an explicit CatalogSettings
and catalog port. Missing settings or catalog is rejected; it never loads host config,
reads environment/secret files or chooses a provider. A standalone mock HTTP preview
also runs without the AIControlCenter source tree. Pydantic v2 is now an explicit
wheel dependency, alongside FastAPI for the HTTP adapter. Pure product/order imports
still need neither host code nor an HTTP framework.

## Host-owned responsibilities
core.shopping.service.ShoppingService is now a composition-only subclass bridge.
It preserves legacy constructor arguments, resolves host settings and provider through
the existing loader/factory, projects only public settings and calls plugin logic.
The full provider settings object is not retained as service.settings: code needing
provider URL/credentials must use the host configuration boundary. The public flags
and frozen-dataclass replacement semantics used by existing UI remain available.
The host bridge is a subclass, not an identity alias of the explicit plugin service.
ProductNotFoundError and all moved error/model/enum/telemetry classes retain identity.

Existing core modules for schemas, health/telemetry, provisional aliases and mock
adapter alias their implementation modules, preserving imports and patch targets.
The host core.shopping.ports package stays a namespace for unrelated provider/auth
ports and re-exports the same catalog contract objects. Non-constructor catalog
methods were AST-compared with ae54f0b: all 15 methods are unchanged.

Actual WooCommerce HTTP adapters, configuration and protected secret resolution,
customer session/owned inquiry persistence, production authorization, audit and
deployment remain in their existing host boundaries. No provider is auto-enabled.
Scheduling and notification authority remain common platform responsibilities.
No business logic or application state moved to Ubuntu.

## Packaging and compatibility
Shopping is 0.3.0; Notes/Assistant remain 0.1.0; Atelier theme remains 0.4.0.
Use the matching Shopping 0.3.0 wheel with this host generation. Prior wheel artifacts
were retained. Do not hot-swap package class definitions into a running process.
Build/install only into a new isolated validation target:

    python -m scripts.build_plugin_wheels --output dist/plugins/catalog-v03
    python -m pip --isolated --disable-pip-version-check install --no-index --no-deps --target .plugin-packages/catalog-v03 dist/plugins/catalog-v03/*.whl

Compatible host dependencies are required; --no-deps prevents modifying them.
The shared interpreter and production PYTHONPATH were not modified. Generated wheel
and test install directories are Git-ignored; source, reproducibility checks and
artifact hashes are tracked. Existing admission/drain/detach semantics are unchanged.

## Verification: 855 passed
- Plugin/domain/catalog/lifecycle/binding suites: 115.
- Catalog/API/read/runtime/schema metadata regression: 418.
- Existing order domain: 9.
- Existing customer session API: 101.
- Owned inquiry API: 68.
- OpenClaw/notification/Twilio offline contracts: 66.
- Health aggregation, dashboard and storefront: 78.

Suites with incompatible process import requirements ran separately. Existing
TestClient/datetime deprecation warnings remain. No release checks were skipped.
Fresh subprocess tests deny host imports, network and DB access while invoking the
standalone mock preview; catalog service is separately tested with FastAPI imports
denied. Exact money strings, options, malformed observations, fixed error responses,
no retry, state aggregation, old/new module identity, credential-free public settings,
lease drain/recovery, individual wheel installs and missing packages are covered.

## Existing test expectation repair
SHOP_API_READ_001 omitted variants=[] from its exact expected payload, although
that field already existed in the pre-extraction ProductResponse. A separate archive
of ae54f0b reproduced the same seven failures (85 other cases passed). The fixture
now includes variants, without changing API code/output. Added an exact list/detail
byte-contract test with a nonempty size option. Assertions, privacy checks and
canonical output validation remain strict. The first new preview import guard also
incorrectly treated idna's relative .core import as the host; the test now rejects
absolute host imports and verifies no core module was loaded. Runtime behavior was
not changed to accommodate this test issue.

## Remaining migration scope
Real WooCommerce/provider adapters, member/inquiry durable storage ownership,
registered background jobs, authenticated external Notes/Assistant operations,
backup/restore, multi-worker coordination and governed production generation switch
remain open. This is catalog/domain implementation separation, not full live shopping
checkout completion or entire legacy application extraction. Production still uses
its existing immutable release and entry point.
