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
