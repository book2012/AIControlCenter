# DEV AI product intake pilot

## Purpose
This milestone validates the first user-upload product ingestion path for the future AI product-management plugin. It keeps the existing 120-item demo catalog immutable and layers user-uploaded DEV products through a separate validated overlay.

## Input
- User-provided product image: camel/brown belted long coat.
- Sizes: S, M, L.
- Inventory: 1 unit per size.
- Price: 300,000 KRW, explicitly supplied by the operator.

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
The supplied price is now `300000` KRW with `price_status=READY`. A DEV upload enters the storefront orderable set only when its validated overlay is enabled, price status is READY and its price is positive.

The isolated DEV WooCommerce product is product #36, SKU `aicc-dev-ag-upload-outer-0001`, status `publish`, category `OUTER`, with the classified tags, attached image and S/M/L variations. Each variation has stock quantity 1 and regular price 300000 KRW. It is the sixth active DEV orderable product.

## Validation
- Relevant storefront/catalog regression: 143 passed.
- Python/JavaScript syntax and `git diff --check`: passed.
- Secret scan: passed.
- Woo product status: publish.
- Woo price state: READY at 300000 KRW.
- Woo variation inventory: S=1, M=1, L=1.
- Woo image attached: yes.
- PROD mutation: none.

## Promotion rule
The promotion rule has been exercised successfully: set the repository overlay price to READY, validate image/category/inventory, update Woo variations without changing stock, publish the Woo parent, then add the stable catalog ID to the private DEV active-product mapping. The order runtime validates uploaded media independently before startup.

## Live DEV activation
Homepage DEV release `fd9cbf8c69ed921b05ad55b7738117f686ea2ac6` is active on port 18080. The live catalog total remains 121 and `ag-upload-outer-0001` renders `300,000원`, three available S/M/L options and the validated uploaded image. Its in-page commerce loader resolves to authoritative Woo product #36. Headless Chrome verified the price, loaded order panel, order button and S/M/L options with no loading-stuck or commerce-error state. The order runtime remains RUNNING and the admin API remains healthy.
