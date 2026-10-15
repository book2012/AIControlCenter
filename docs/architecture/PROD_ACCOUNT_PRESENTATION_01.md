# PROD account presentation 01

## Scope

- Candidate plugin version: `0.19.2`.
- Host gate: `agachichi.duckdns.org` only.
- Presentation: branded login header/footer and responsive account styling.
- Authentication remains WooCommerce-owned. Customer registration and DEV phone verification are excluded.
- Logout uses WooCommerce's `customer-logout` account endpoint with its nonce. It does not call `wp-admin/admin-ajax.php`, which the public ingress blocks.
- Account UI asset loading is limited to WooCommerce account pages.

## Validation state (2026-10-15)

- PROD public `/`, `/shopping/categories`, `/shopping/products`, `/my-account/`, and `/my-account/lost-password/` return HTTP 200.
- `/my-account/register/`, `/shopping/orders`, `/wp-login.php`, and `/wp-json/` return HTTP 404.
- Current PROD plugin remains immutable `0.19.1`; this `0.19.2` candidate has not been activated.
- Account suite and associated runtime/promotion contracts: 40 passed.
- PHP syntax checks passed for the plugin entrypoint and account presentation class.
- Live PROD login has a form and no signup link, but still renders the old “My account – Bokstory” title until the candidate is released.

## Release requirements

1. Commit the candidate on its feature branch and pin its full commit in the read-only release contract.
2. Materialize the plugin from the clean Git archive into a commit-addressed immutable PROD release.
3. Activate only the plugin bind mount; retain the previous immutable release for rollback.
4. Verify the branded title/assets, account login, nonce-backed logout endpoint, signup denial, product catalog, and order isolation.
5. Keep DEV/PROD WooCommerce accounts, orders, inventory, and product registration data separate. Never provision customer signup or real SMS as part of this release.
