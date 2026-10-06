# DEV AI product intake pilot

## Purpose
This milestone validates the first user-upload product ingestion path for the future AI product-management plugin. It keeps the existing 120-item demo catalog immutable and layers user-uploaded DEV products through a separate validated overlay.

## Input
- User-provided product image: camel/brown belted long coat.
- Sizes: S, M, L.
- Inventory: 1 unit per size.
- Price: not supplied.

## AI-assisted classification
- Catalog ID: `ag-upload-outer-0001`.
- Name: `카멜 벨티드 롱 코트`.
- Category: `OUTER`.
- Color terms: `카멜`, `브라운`.
- Tags: `벨티드`, `롱코트`, `카멜`, `브라운`, `가을`, `겨울`, `클래식`.
- Storefront presentation tags: `#롱코트 #벨티드 #카멜브라운`.

The classification is a DEV editorial/catalog draft derived from the supplied image. Material composition is not inferred or claimed.

## Media handling
The supplied screenshot was cropped only to remove phone/social-app UI and resized for the DEV storefront. The garment itself was not restyled or regenerated. The resulting repository media is validated by a dedicated DEV upload manifest and SHA-256 before serving.

## Catalog architecture
`brands/agachichi/catalog/dev-upload-products.json` is a DEV-only upload overlay. `DemoCommerceCatalogAdapter` loads it only in the real lookbook DEV composition; the base Orange Coco demo catalog remains unchanged. A malformed upload media manifest fails closed for the upload without taking the validated base presentation media offline.

## Commerce gate
Price was not supplied, so the overlay uses `price_status=PENDING` and a zero sentinel that renders as `가격 준비 중`; it never renders as `0원`. The product is intentionally absent from the orderable-product allowlist.

The isolated DEV WooCommerce product is product #36, SKU `aicc-dev-ag-upload-outer-0001`, status `draft`, category `OUTER`, with the classified tags, attached image and S/M/L variations. Each variation has stock quantity 1 and an empty regular price. It is not an orderable product.

## Validation
- Relevant storefront/catalog regression: 143 passed.
- Python/JavaScript syntax and `git diff --check`: passed.
- Secret scan: passed.
- Woo product status: draft.
- Woo price state: PENDING.
- Woo variation inventory: S=1, M=1, L=1.
- Woo image attached: yes.
- PROD mutation: none.

## Promotion rule
Providing a sale price is a separate explicit action. Promotion must set the price in the upload record and Woo variations, revalidate stock/image/category, then add the stable catalog ID to the DEV orderable mapping. Until that promotion succeeds, the storefront remains browse-only for this product.

## Live DEV activation
Homepage DEV release `4b961ec05639a9a00828ce681304e967eaa42d97` is active on port 18080. The live catalog total is 121 and `ag-upload-outer-0001` is visible with `가격 준비 중`, three available S/M/L options, the validated uploaded image, and no order commerce panel. Search for `벨티드` returns the product. The order runtime remains RUNNING and the admin API remains healthy.
