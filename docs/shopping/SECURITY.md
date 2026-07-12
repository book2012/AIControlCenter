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
