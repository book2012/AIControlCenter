# DEV and PROD release boundaries

## Roles

- DEV is where features, storefront behavior, checkout flows, and product intake are tested.
- PROD uses pinned code releases and its own WooCommerce products, Woo IDs, binding file, inventory, and order data.
- A DEV product becomes a PROD product only through the explicit PROD registration command. It receives its own Woo product and variation IDs and an aicc-prod SKU. New inventory starts at zero while inventory_pending is true.
- DEV test inventory is not copied to PROD. PROD product quantities are read from production WooCommerce variations.

## Product registration

Plan first:

/Users/kyouhan/AIControlCenter/.venv/bin/python ops/macos/shopping/prod_upload_product_register.py --catalog-id ag-upload-bottom-0002

The default command is read-only. After reviewing the product, price, options, and media, register it explicitly:

/Users/kyouhan/AIControlCenter/.venv/bin/python ops/macos/shopping/prod_upload_product_register.py --catalog-id ag-upload-bottom-0002 --apply-prod

The command asserts the production Docker project and database, creates only the matching product and variations with zero stock, verifies media hashes and order count, and stages private binding/projection candidates. It does not create orders, change existing product quantities, or activate a candidate release.

Use the same plan/review/apply steps for each new PROD product. The product source must first exist as a validated upload in the catalog; the PROD registration and Woo binding remain an explicit separate operation.

## Code promotion and DEV sync

1. Pin a clean commit in DEV and run the relevant tests.
2. Build a production release from that exact commit in an isolated worktree.
3. Apply only reviewed PROD-specific guards and PROD host settings. Preserve Telegram bot separation.
4. Validate the candidate and promote the immutable PROD release.
5. After PROD health and public read paths pass, advance DEV's release pointer to the same code commit. Keep DEV data, credentials, customer data, and inventory in the DEV environment.
6. Record both environment pointers and catalog hashes in AIControlCenterRuntime/version-matrix.json.

DEV is synced to the PROD code version after a successful PROD update; PROD catalog registrations and business data are never copied back into DEV.

## PROD account login ingress

The storefront account link uses WooCommerce's existing `/my-account/` login page.
PROD Caddy may proxy that page and its static CSS/JS/image assets to the isolated
WordPress upstream. It may proxy only the `aicc_account_navigation` GET and
`aicc_account_logout` POST AJAX actions. Keep other WordPress admin, REST, and
WooCommerce management paths unavailable at the public ingress.
