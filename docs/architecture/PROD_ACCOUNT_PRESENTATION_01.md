# PROD account presentation 01

## Scope

- Active plugin version: `0.19.2`, commit `7dda8c9e012208977cf26ed2b563d8111c56c27e`.
- Host gate: `agachichi.duckdns.org` only.
- Presentation: Agachichi document title, branded login heading/header/footer, and responsive account styling.
- Authentication remains WooCommerce-owned. Customer registration and DEV phone verification are excluded by the current PROD customer-account policy; the PROD homepage exposes login and order lookup, not signup.
- Logout uses WooCommerce's `customer-logout` account endpoint with its nonce. It does not call `wp-admin/admin-ajax.php`, which public ingress blocks.
- Account UI asset loading is limited to WooCommerce account pages.

## Production verification (2026-10-15)

- Active plugin is mounted read-only from the commit-addressed immutable release. WordPress and database named volumes were preserved; only the WordPress container was recreated.
- `/`, `/shopping/categories`, `/shopping/products`, `/my-account/`, and `/my-account/lost-password/` return HTTP 200.
- `/my-account/register/`, `/shopping/orders`, `/wp-login.php`, and `/wp-json/` return HTTP 404.
- Account document title is `로그인 – agachichi`; login form and Agachichi heading are present. Account CSS, storefront CSS, and account JS return HTTP 200. There are no legacy Bokstory domain references or signup links in the account page.
- Product API reports 21 products; category API reports 7 categories.
- The WooCommerce logout endpoint recognizes the account path. A logged-in session was not available for an end-to-end session termination test.
- Focused tests: 54 passed. PHP syntax checks passed for the plugin entrypoint and account presentation class.
- Previous immutable plugin `0.19.1` release remains available at commit `ee229261459e24d1a2d73b39bbbb8e2fa4042ba9` for rollback.

## Environment separation

DEV retains its separate account plugin and test signup/phone-verification behavior. The PROD-only host gate prevents this presentation class from enabling or changing DEV registration. WooCommerce accounts, orders, inventory, and product registration data remain environment-local. No order, payment, inventory, or SMS operation was performed during this release.
