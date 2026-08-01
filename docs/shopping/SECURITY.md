<!-- SHOPPING_M4_START -->

## M4 Security

- Catalog integration is read-only.
- WooCommerce credentials must never be committed.
- Repository Secret files:
  - deploy/shopping/.env
  - deploy/shopping/.env.admin
  - deploy/shopping/.env.woocommerce
- Runtime Secret:
  - /etc/aicontrolcenter/shopping.env
- HTTP OAuth is permitted only for the local development connection.
- Production requires HTTPS and API Key rotation.
- No real customer, payment, or order data is allowed in the HTTP development environment.
<!-- SHOPPING_M4_END -->

<!-- SHOPPING_M5_START -->

## M5 Storefront Security

- WordPress API requests use the internal Docker host gateway.
- WooCommerce Consumer credentials are not available to the WordPress Plugin.
- The Plugin calls AIControlCenter public read endpoints only.
- Search input is sanitized before forwarding.
- Output is escaped before rendering.
- API redirection is disabled in the Plugin client.
- WordPress Presentation Cache stores only read responses.
- No customer, order, payment, or write credentials are exposed to Storefront.
<!-- SHOPPING_M5_END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## SHOP-01E3C Secure WooCommerce Read Runtime

AIControlCenter now provides a reusable secure runtime loader for the
existing WooCommerce read-only credential file.

The loader validates:

- a regular non-symlink credential file
- current-user ownership
- file mode `0600`
- direct parent mode `0700`
- exact credential keys
- read-only WooCommerce API permission

Credential values are not copied into Git, LaunchAgent plist files or
the process environment.

Runtime selection uses the non-secret profile:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

The profile is not enabled persistently by this task. Persistent
LaunchAgent activation requires a separate operational authorization.

The canonical WooCommerce target currently has zero products and one
product category. This is a valid empty Commerce Engine state, not an
adapter failure.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## ProductDraft Security Boundary

AI suggestions are untrusted optional inputs and cannot approve. Only a `HUMAN` reviewer can decide an exact revision. New revisions inherit no decision; revoked approvals cannot be reused. Contracts exclude credentials and raw prompt secrets. Deployment intent requires separate authorization and audit references but never authorizes execution. Production writes remain `NOT_AUTHORIZED`.
