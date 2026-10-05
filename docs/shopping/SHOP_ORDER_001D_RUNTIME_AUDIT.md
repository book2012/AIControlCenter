# SHOP_ORDER_001D effective DEV / PROD runtime audit

Observed 2026-10-06 (Asia/Seoul). Read-only: effective Caddy configuration, loopback HTTP GET, sanitized container identity/mounts/plugin inventory and SQL SELECT inside a read-only transaction. No runtime restart, edge change, provider write or database mutation.

## Effective topology

| Surface | Effective target | Catalog / database state |
|---|---|---|
| dev.bokstory.duckdns.org | Mac AIControlCenter 127.0.0.1:18080 behind Basic Auth | Demo catalog; /homepage/storefront 200; /wp-admin/ 404 |
| bokstory.duckdns.org | WordPress 58082 + catalog API 58081 | Five mock products; WooCommerce active but zero WordPress product rows |
| Isolated visual preview | WordPress 55273 + mock-api.py | Separate preview DB; WooCommerce absent; zero product rows |

DEV and PROD application routes are separate. Preview and PROD databases are also separate: `storefront-preview-6eaaaef4-database` / `storefront_preview` versus `ai-shopping-database` / `aicc_shopping`, on distinct internal Docker networks. This does not establish a working DEV WooCommerce order backend.

## Why the administrator URL failed

The DEV domain forwards to AIControlCenter, which is not WordPress. `/wp-admin/` therefore returns 404. Earlier advice to use the DEV domain's `/wp-admin/` inferred a backend that was not present. PROD and visual-preview WordPress administrator endpoints exist on loopback and return login redirects; public PROD administrator access remains blocked. Do not expose PROD admin or point DEV test keys at PROD to resolve this mismatch.

## Actual order / migration state

The selected '소프트 린넨 블라우스' is canonical demo item `oc-demo-top-0001`, source `demo`, in_stock true. It is not an actual WooCommerce product ID. PROD WordPress has WooCommerce active and 16 Woo-related tables, but no product rows. The visual preview has no WooCommerce plugin/tables. This inventory does not claim the contents of unrelated databases or historical backups.

Both current Mac APIs return 404 on GET `/shopping/orders` and `/shopping/auth/session`; DEV OpenAPI contains no order/auth routes. The 001D implementation remains a clean pushed repository candidate; its explicit DEV factory is not mounted into either current runtime. No actual order-ledger database migration or supervised order dispatcher/poller has been performed.

The existing media audit found 121 deployed assets intact, while the PROD mock catalog does not match the demo image mapping. File deployment and catalog/provider migration are distinct; the latter remains incomplete.

## Telegram

Real Bot API identity and private recipient were verified. One authorized connection test was successfully sent to Damian by `mommychichi_bot`; fixed chat/user IDs reside only in local owner-readable private configuration. No real order notification, payment or provider order was created. Dedicated order polling has not been activated.

## Implementation consequence

Provision a dedicated durable DEV WooCommerce + DB runtime, preserving existing visual preview and PROD. Establish the test product/variant and scoped API key inside that DEV store. Keep business/session/authority/ledger policy on the Mac. Then mount authenticated DEV order composition and fixed-recipient supervised Telegram integration, validate one unpaid pending order through operator review and owner status, and only afterward prepare a separate immutable PROD promotion gate. The demo product cannot be passed to WooCommerce as a numeric provider product ID without an explicit catalog migration/mapping.

Exact observations are in `SHOP_ORDER_001D_RUNTIME_AUDIT.json`. The existing root repository dirty work was observed and left untouched. This audit changes only documentation on the 001D feature branch.
