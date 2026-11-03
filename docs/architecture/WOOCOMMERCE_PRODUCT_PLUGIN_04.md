# WooCommerce product-read extraction — Shopping plugin 0.4.0

Date: 2026-11-03 (Asia/Seoul)
Status: product-read logic extracted and isolated validation complete.
No live WooCommerce request, credential read, actual checkout or production change.

## Ownership

Plugin implementation:
plugins/shopping/src/aicc_plugin_shopping/adapters/woocommerce_product_read.py

The plugin owns product ID/page validation, response JSON handling, product/variant
normalization, canonical list/detail visibility and bounded product-read health.
A WooCommerceProductReadPort plus an explicit authorize callback are required.
There is no default HTTP client, base URL, credential, signer, discovery, retry,
scheduler or deployment operation in this implementation. It imports neither core,
ops, integrations, requests, FastAPI nor Pydantic and runs behind a synthetic read
port without the host tree or an HTTP framework.

Platform ownership remains:
- WooCommerce base/connect URL and destination trust configuration.
- Consumer key/secret resolution and storage, OAuth/basic signing.
- Transport timeouts, proxy/environment isolation, redirects disabled, request-header
  scrubbing and no retry authority.
- External-read policy and approvals, customer/order authorization and audit.

The existing core.shopping.adapters.woocommerce_rest.WooCommerceRESTAdapter is a
compatibility subclass. Its initializer, _uses_https, _oauth_params, _request,
_authorize_product_read, raw order read, category read and search methods were
AST-compared with e0585d1: all eight are unchanged. The transport source file is
byte-identical. The host still overrides request/authorization and supplies its
existing transport; it never uses the new adapter's standalone port defaults.
A transport_kind property preserves the existing health label. Public product
conversion behavior and WooCommerceAPIError import/catch identity remain compatible.

## New explicit product-read port
Construct WooCommerceProductReadAdapter(port, authorize=callback). The port exposes
read(path, params=...) only; endpoint selection, credentials and real I/O belong to
its reviewed host implementation. The callback must return exactly True for each
actual read. False, None, truthy non-bool and exceptions deny before port access.
This explicit adapter permits only /products and canonical numeric /products/{id}
paths. Authentication query keys and non-product requests are rejected. Its port is
not an arbitrary URL proxy or a generic WooCommerce/order reader.

Authorization receives a query copy and cannot rewrite the dispatched query. Each
accepted call invokes the port once. HTTP failure classes are normalized; port
exception text and context are not propagated. Timeouts and transport exceptions
become bounded WooCommerceAPIError projections; 404 and private visibility remain
non-public products. Raw vendor payload methods are internal provider seams, not
new public endpoints. The caller-provided port and authorizer are trusted platform
code; this is not a sandbox for untrusted Python implementations.

The legacy host's category/search/raw-order code is intentionally still host-owned:
those operations have different authority and contract scopes. This step does not
claim full provider extraction or expand their existing access. No new production
binding is created. Resource ownership stays with the explicit ModuleInstance
start/close hooks; detaching an adapter does not implicitly close a shared host
transport or delete WooCommerce data.

## Packaging
Shopping wheel: 0.4.0; Notes/Assistant: 0.1.0. This Shopping Python wheel is a distinct
artifact from the Atelier WordPress theme, which also happens to be version 0.4.0.
The Gumroad product/theme files and commercial settings were not modified.

    python -m scripts.build_plugin_wheels --output dist/plugins/woo-v04-verified
    python -m pip --isolated --disable-pip-version-check install --no-index --no-deps --target .plugin-packages/woo-v04-verified dist/plugins/woo-v04-verified/*.whl

Use a fresh isolated target and matching host/plugin generation. No shared Python
installation, live service path, launchd, Caddy, DNS or environment setting changed.
Generated artifacts and targets remain ignored; reproducible source and hashes are
tracked. Previous development wheel outputs were retained, not overwritten as a
published release. Hot package replacement in a running commerce process is unsupported.

## Verification: 889 passed
- Plugin/read-port/domain/catalog/lifecycle/binding suites: 149 (34 new read-port cases).
- Existing catalog/API/read/runtime/capability cases: 418.
- Order domain: 9.
- Customer session API: 101.
- Owned inquiry API: 68.
- OpenClaw/notification/Twilio offline contracts: 66.
- Health/dashboard/storefront: 78.

Suites that prohibit legacy app imports ran separately. No required checks skipped;
existing TestClient/datetime deprecation warnings remain. Tests include exact product
bytes, decimal strings/options, trusted host signing/read policy regressions, timeout
and no retry, error scrubbing, denied approval before I/O, invalid IDs/pages before
approval, non-product scope denial, private/not-found products, port-only imports,
package install/absence isolation, and attach/drain/detach/recovery. Pure mock/synthetic
fixtures only; no actual customer/order/provider read or network operation.

## Remaining work
Host-owned category/search/raw-order provider scopes, durable session/inquiry storage
and job ownership, actual Notes/Assistant authentication, backup/restore, multi-worker
coordination and governed production-generation migration remain open. This is a
product-read boundary extraction, not full live service/checkout completion.
