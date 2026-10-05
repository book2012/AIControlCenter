# Isolated DEV order validation and production migration gate

## Architecture

AIControlCenter on the Mac owns authentication, order authority, durable operation state and Telegram review. WooCommerce is the commerce engine. The new `aicc-order-dev` Docker project uses its own MariaDB database, named volumes and networks. Existing production and preview containers were preserved. No DEV database, synthetic customer, verification receipt, order, API key or bot token is a production migration input.

Canonical Core WooCommerce URL policy remains unchanged. An explicitly injected DEV transport verifies a private localhost TLS certificate and targets only the isolated WooCommerce facade. DEV credentials create synthetic verification evidence for one test account; they do not establish phone verification.

The Caddy overlay selects only DEV order paths after the existing Basic Auth handler. All non-DEV configuration is checked unchanged. Original `/homepage/storefront` remains the demonstration catalog; the live single-product order preview is a separate DEV path. Only the blouse is mapped to real isolated WooCommerce variations and its manifest-verified photo. The full catalog has not been migrated.

## Verified behavior

- 662 Python tests passed; 20 existing deprecation warnings. 12 Node UI tests passed.
- Isolated Chrome exercised UI, HTTP, simulated Telegram review and customer status with one simulated provider write. This test made no external provider requests.
- Separately, a real isolated DEV WooCommerce pending, unpaid order #14 was created for KRW 29,000. Exact replay returned HTTP 200 without another create.
- The real Telegram bot sent order notification message #6. The verified human operator sent the confirmation command: review is CONFIRMED, confirmation notification message #8 is SENT, and the existing customer session returns HTTP 200 with COMPLETED / CONFIRMED for order #14.
- Invalid customer credentials returned 401; invalid CSRF returned 403 before order creation.
- After restarting the owned DEV API, the existing customer cookie still fetched the same operation with HTTP 200. The notification remained SENT with message #6.
- Explicit durable session recovery is opt-in; the default boundary still denies missing process bindings. Recovery checks stored credential identity, expiry, revocation and current customer state.
- DEV login and preview remain protected by existing edge Basic Auth. Production homepage returned 200 and its order path 404. No production mutation was performed.

## Operator runbook

DEV entry: https://dev.bokstory.duckdns.org/dev-order/login . Test username: `aicc-dev-test-customer`. The password is stored privately in `/Users/kyouhan/.config/aicontrolcenter-dev-order/commerce.private.json`; do not publish it. Existing DEV Basic Auth is an additional protection.

The actual human review completed using `/order_confirm 0dbcf262cdb2bae510b71bb6` to @mommychichi_bot in the verified private chat. Confirmation changes review state only; it does not mark the WooCommerce order paid or fulfill it.

The private files and logs are local and excluded from Git. DEV SQLite backups are in `/Users/kyouhan/AIControlCenterRuntime/dev-order/backups` with private permissions; hashes are in the validation JSON. The full Caddy pre-overlay configuration is backed up privately. Never rerun the live probe after `post_attempted` is true: inspect the existing saved operation instead.

Provisioning: `python -m ops.macos.shopping.dev_order_provision`. Run only against the explicitly isolated DEV project. The provisioner copies the existing WooCommerce package read-only into DEV and fixes DEV ownership, avoiding changes to Colima shares or the production plugin. The HTTPS facade and API entrypoints are `dev_order_https_proxy.py` and `dev_order_runtime.py`; edge application is `dev_order_edge.py`.

## Production migration gate — BLOCKED

Do not activate this DEV setup on bokstory.duckdns.org. Outstanding work is production phone authentication, approval and validation of all real products/variants/photos, service supervision, a persistent reviewed edge deployment, and production backup/rollback rehearsal. Current DEV API/facade processes are not yet installed as launchd services; the applied live edge overlay must be reviewed for persistence across Caddy restarts. Public authenticated browser end-to-end validation remains outstanding.

The future production release must use production-specific credentials, identities, fresh runtime state, approved provider mappings and an explicit production deployment package. Preserve the current production container IDs, volumes and routes until the validated release is ready. Record the candidate Git commit, migration plan, backup and rollback proof before activation. A desired-state package alone is not activation authorization.
