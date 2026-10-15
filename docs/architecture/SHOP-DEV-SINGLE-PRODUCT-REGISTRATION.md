# Isolated DEV single-product registration

Status: implemented and locally validated. Candidate activation is separate.

## Ownership

- WooCommerce remains the commerce source of truth for products, prices, variations and stock.
- AIControlCenter owns registration validation, DEV target isolation, request orchestration, safe candidate staging and evidence.
- The Git catalog and image manifests own storefront copy and media references.
- This workflow targets only `aicc-order-dev` through Docker context `colima-aicontrolcenter-commerce`.
- No ProductDraft API, PROD, Ubuntu, public release or Homepage activation is part of this registrar.

## Flow

1. Read `brands/agachichi/catalog/dev-upload-products.json` and the DEV upload/gallery manifests.
2. Validate the exact product ID, user-upload source, approved price state, option matrix, inventory state, image paths, SHA-256 digests and required gallery roles.
3. Inspect the expected DEV WordPress/database container labels and volumes.
4. Query WooCommerce by deterministic SKU `aicc-dev-{catalog_id}`. Existing matching products are verified and reused; mismatched SKU/catalog/variation/media bindings fail closed.
5. With `--apply-dev`, stage the verified images inside the DEV WordPress container, create the variable product and variations, then read everything back. Compare order count before/after.
6. Stage product binding and hash-bound projection candidates under private DEV runtime paths. Do not overwrite active runtime configuration.

## State boundary

The default command is read-only and emits JSON. `--apply-dev` is the only mutation switch. It creates WooCommerce objects in isolated DEV, then writes private candidate mapping/projection/evidence files with mode `0600`. Candidate data does not change the running order API or Homepage. Git source changes and the existing immutable DEV release procedure remain separate.

Inventory marked pending must be zero for every variant. Such products remain unavailable. If registration fails after WooCommerce begins writing, the tool returns a generic inspection-required error and refuses to create a duplicate on retry; it does not attempt rollback or resend.

## Verification

- Pure input/media/options validation: `tests/test_dev_product_registration_validation.py`.
- Mapping/projection candidate checks: `tests/test_dev_product_registration_operator.py`.
- Runtime validation command:
  `python3 ops/macos/shopping/dev_upload_product_register.py --catalog-id <id>`.
- DEV registration command (only after product review):
  `python3 ops/macos/shopping/dev_upload_product_register.py --catalog-id <id> --apply-dev`.

Both registration test files use the Python standard library; tests perform no live WooCommerce writes.

## 2026-10-15 intake verification

`ag-upload-bottom-0002` (베이지 플라워 레이스 롱 스커트) was registered in isolated DEV WooCommerce as product #186 at user-approved temporary KRW 79,000. The only option is beige with inventory `0` and `inventory_pending=true`, so it is unavailable for purchase. The upload source and three AI-generated presentation images are SHA-bound. Product and image metadata were read back successfully and the Woo order count was unchanged. Private runtime mapping and projection candidates are staged; Homepage/order API activation remains pending.

The first plan attempt exposed a registrar integration defect: the PHP harness was not passed to PHP CLI, which received only the JSON payload. The operator now executes the harness with `php -r` and leaves JSON on stdin. A regression test covers that boundary; the final focused suite has 13 passing tests.

The added upload row changed the full catalog hash and initially caused the strict DEV test-stock overlay to fail closed. The prior catalog comparison confirmed this was only the new skirt row; no existing product row or test-stock quantity changed. Updated only `dev-test-stock.json.catalog_sha256` to the new catalog hash. The legacy batch still selects 17 reviewed records and filters out `registration_method: single_product`. The 30-test registration/storefront/media/batch-boundary suite passes. The staged DEV projection applies the new row at KRW 79,000 with beige inventory zero and pending. Activated in immutable DEV release `c010f1d78ba0752b9d59cb0e6fcf89d36457b8fb`; live listing/PDP and all three gallery assets return HTTP 200, while stock stays zero and unavailable. PROD remains untouched.


## DEV activation result — 2026-10-15

Homepage and API both run the immutable c010f1d release. The live listing returns 21 products and includes product #186 at KRW 79,000; beige stock and variant availability are false, and the detail page communicates pending inventory. All three bound gallery assets return HTTP 200. DEV API health reports operator bridge/product management running, Telegram poller external, and order SMS configuration required. No order was created.
