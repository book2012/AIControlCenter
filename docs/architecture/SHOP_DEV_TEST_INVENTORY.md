# SHOP DEV test inventory

The user authorized arbitrary inventory for testing. The 17 recently uploaded products receive Color × Size combinations: clothing S/M/L; bags/accessories FREE; 3 units for each of 60 combinations, 180 initial units. The two confirmed coats and the other five established DEV products retain their current stock. No PROD, real sale inventory, price or size assertion is implied.

## JSON and provider ownership
The original pending-photo catalog remains intact. dev-test-stock.json is an explicit DEV overlay bound to the original catalog SHA256. It rejects wrong environment, wrong scope, changed source, wrong quantity and undeclared sizes. Preview composition applies it; old pending-stock regressions use test_inventory=False explicitly.

WooCommerce remains authoritative for orders and remaining stock. dev_test_stock_register.py is read-only by default and requires --apply-dev plus isolated context/project/volume/database identity for mutation. It validates all 17 provider IDs and SKUs. Original zero-stock color-only variations are retained privately with a retirement marker; no variation or order is deleted. New combinations are created with managed stock, quantity 3, no backorders and the temporary price. Existing combination quantities are validated and preserved on replay. A transaction and lock protect initialization; order counts must remain unchanged. Candidate runtime bindings are staged privately and are not credentials or repository artifacts.

## Customer flow
Canonical color buttons and the size group form one selection. The hidden provider select carries only the exact Color / Size variation. Missing or unavailable combinations clear that select and disable add/order; picking another valid combination recovers. Provider-to-UI changes keep both dimensions and the matching color photo synchronized. Cart and final review display both dimensions. Quotes check current per-variation quantity; authoritative preparation/confirmation rechecks stock. Existing WooCommerce order confirmation/reduction behavior remains in place.

## Validation and preservation
205 Python regressions plus real Chrome combined-option checks, legacy pending color/cart checks and phone/address/confirm/Telegram fake-provider checkout checks. No real order, SMS or Telegram test message is created. Snapshot the protected seven products and eight existing orders before provider mutation, then compare after. Apply twice to verify replay creates no replacements or resets. Live DEV checks use only GET plus the anonymous quote route; no phone, order, confirmation or payment POST is permitted by the test proxy.

## Activation and rollback
Commit and push the feature branch first. Apply only isolated Woo test inventory, stage the 24 bindings, preserve private config/current manifest backups. Activate the immutable homepage release first while the old API still denies pending products; then stop the owned old order API, wait for the poller lease to release, atomically switch the private DEV bindings, and start the new API from the same release. Require unique owned listeners, matching cwd, DEV/RUNNING health and all combinations.

If API activation fails, restore the old config and old homepage manifest and restart only owned DEV processes. The old pending flag keeps the newly provisioned test inventory unavailable; preserved provider rows and backups allow inspection. No Caddy or PROD mutation is part of activation.
