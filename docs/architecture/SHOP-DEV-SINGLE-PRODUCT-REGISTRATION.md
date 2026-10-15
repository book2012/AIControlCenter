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

Both new test files use the Python standard library. No live product registration is performed by the tests.
