# Shopping domain package extraction — 0.2.0

Date: 2026-11-03 (Asia/Seoul)
Status: pure product/order domain extraction and isolated validation complete.
Production and real service/authentication connections remain unchanged.

## Source ownership

| Responsibility | New authoritative implementation | Compatibility import |
| --- | --- | --- |
| Product / ProductVariant | aicc_plugin_shopping.models | core.shopping.models |
| OrderSnapshot / OrderLineItem / OrderListQuery / OrderContractError | aicc_plugin_shopping.order_core.domain | core.shopping.order_core.domain |
| OrderReadPort | aicc_plugin_shopping.order_core.ports | core.shopping.order_core.ports |
| OrderService / OrderNotFoundError | aicc_plugin_shopping.order_core.service | core.shopping.order_core.service |

The product/order implementation is no longer duplicated in the host. The old
modules re-export the exact same class objects from the installed shopping wheel.
Strict type identity checks therefore retain their intended meaning across old
and new import paths. Existing service validation and data fields were copied
without semantic changes. No database schema, record or serialized payload format
was migrated. Module-qualified class names now refer to the plugin; cross-version
pickle workflows are not supported or claimed by this verification.

The package root uses lazy exports. Importing the product/order domain does not
import FastAPI, host core, ops, integrations, HTTP clients, SQL or credentials.
The HTTP preview and explicit authenticated binding adapters remain optional
exports and still require a compatible host. Pure domain code itself needs only
Python's standard library. The plugin is not an independent commerce server.

## Version and installation boundary
Shopping wheel is now 0.2.0; Notes and Assistant remain 0.1.0. Atelier theme remains
0.4.0. Host plugin API is still v1: this move preserves adapter/import contracts.
The updated host compatibility imports require the 0.2.0 shopping wheel whenever
legacy Shopping functionality is used. An old 0.1.0 wheel lacks the extracted domain;
it is not an appropriate dependency for this host generation. Common modular
all-detached startup still requires no optional plugin packages.

Build to a version-scoped directory, preserving prior artifacts:

    python -m scripts.build_plugin_wheels --output dist/plugins/domain-v02

Install only for isolated testing, into a new empty target:

    python -m pip --isolated --disable-pip-version-check install --no-index --no-deps --target .plugin-packages/domain-v02 dist/plugins/domain-v02/*.whl

No shared interpreter, launchd configuration or production PYTHONPATH was changed.
Deployment must install compatible plugins before starting a reviewed new host
process generation. Hot-swapping class definitions into a running commerce process
is not supported. Attach/detach admission/drain semantics remain unchanged.

## Verification: 555 passed, no skipped release checks
- Domain/package/catalog/lifecycle/binding suites: 104.
- Existing order-core contracts: 9.
- Catalog/runtime/read-health/capability regressions: 207.
- Existing customer session API: 101.
- Owned inquiry API: 68.
- OpenClaw/notifications/Twilio offline contracts: 66.

Suites that prohibit legacy app imports ran in independent processes, retaining
existing isolation assertions. The 0.2.0 wheel was installed in a fresh local target.
Fresh-process domain tests deny host/HTTP/SQL imports; pure order lookup still works.
Old/new import class identity, rejected untrusted order result shapes, exact money
strings, auth denial, all three individual wheel installs, missing-package startup,
version rejection, RECORD hashes, deterministic builds, drain and reattach are covered.
Existing TestClient/datetime deprecation warnings remain; no dependency upgrade was made.

This is static/fixture/in-process validation, not live commerce E2E. No real customer,
order/payment, SMS, Telegram, private note, provider credential, Ubuntu action or
production runtime change occurred. Original dirty source/index preservation was
checked separately before commit.

## Still owned by existing boundaries
- The full ShoppingService, provider adapters, runtime/persistence, inquiry/session
  authority and deployment/governance code remain at their existing host paths.
- Authentication/authorization was not weakened or replaced with a permissive
  fake. Tests inject synthetic authorities only in isolated fixtures.
- Notification routing, approval/audit/deployment control remain common platform
  responsibilities; transport/provider work remains behind explicit ports.
- Real authenticated Notes/Assistant integration and production generation change
  remain open. The package release does not imply full legacy-domain separation.
