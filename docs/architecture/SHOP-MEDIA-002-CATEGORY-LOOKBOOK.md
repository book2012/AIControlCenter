# SHOP_MEDIA_002 — Orange Coco category lookbook

The preview launcher composes a presentation-only 120-item fixture at
`brands/orange-coco/catalog/lookbook-preview`. It preserves the original
92-item Orange Coco catalog and adds 28 explicitly marked fictional demo
records so each TOP, BOTTOM, OUTER, DRESS, BAG, and ACC category has 20 read
items. Shopping response schemas and the original catalog package are
unchanged; production and WooCommerce state are not involved.

`core/homepage/storefront_media.py` is the replaceable media adapter. It only
serves a manifest-approved local JPEG when the generated file exists, then
falls back to the existing repository photo route for planned assets. It never
turns media metadata into commerce data or a remote proxy. The homepage shows
four samples per category below NEW/BEST; category search pages paginate the
20 canonical preview records.

The deterministic manifest is
`brands/orange-coco/assets/media/SHOP_MEDIA_002.json`. It contains 120 unique
target mappings, model profile/pose/crop/prompt fields, generation provenance,
status, and checksums. Built-in image generation has produced 20 assets; 100
remain `PLANNED`, with no fake generated claim.
Pexels CDN access was tested, but indexed search/download metadata could not be
verified at the required scale in this environment, so zero stock assets were
imported and no unverified external image is claimed as complete.

Validation: 93 focused storefront/preview tests passed; 350 relevant
Homepage/Shopping regressions passed; local preview smoke checks passed for
Home, Search, category page 2, known/unknown PDP, hero, and canonical product
GET. `git diff --check` passed. Browser automation is `NOT_RUN` because
Playwright is not installed and no package was installed.
