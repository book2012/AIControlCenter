# Orange Coco brand media — SHOP_MEDIA_001

This directory owns storefront editorial media independently of WordPress or
WooCommerce deployment. The homepage hero is
`storefront/hero-boutique.jpg`, served by the fixed read-only route
`/homepage/assets/storefront/hero-boutique.jpg`.

The hero is original generated demo artwork: a fictional adult female model in
a warm ivory/orange clothing boutique. It is not a canonical product image.
The built-in `image_gen` tool generated the hero and seven product photographs;
the selected images were visually inspected and encoded as JPEG with `sips`
formatOptions 88. No package installation, remote hotlink or image proxy is used.

[SHOP_MEDIA_001.json](SHOP_MEDIA_001.json) is the current deterministic media
inventory. It records the full prompt and generation tool for each completed
asset, original generated-artifact checksum, final JPEG checksum, local target
and photo route. Product replacements retain their existing plugin repository
paths and exact JPG filenames. They do not depend on plugin deployment to be
served by the local Homepage photo route.

Current completion:

- Hero: **1 completed**, brand-owned path above.
- Product photographs: **7 replaced / 92**, **85 pending**.
- Completed product IDs: `oc-demo-top-0001`, `oc-demo-top-0002`,
  `oc-demo-top-0003`, `oc-demo-top-0004`, `oc-demo-top-0008`,
  `oc-demo-top-0012`, `oc-demo-top-0016`.
- These cover all eight NEW/BEST homepage slots, with top-0004 in both
  canonical collections. Collection membership was not changed for imagery.

For every pending image, the manifest lists the exact existing `target_path`,
current checksum and `candidate_path`; all 85 existing files remain present.
Prepare one reviewed portrait JPEG per pending product, following the shared
editorial brief and canonical name/description. Then replace that exact target,
update its actual provenance in the existing `asset-manifest.json`, update
this inventory's status/checksums/counts, and run the focused media/route tests.
Never retain old photographer attribution on a generated replacement. Previous
provenance is retained under `previous_asset` for the seven completed swaps.

The active 92 products are demos, not actual products offered for purchase.
No gallery, variant, size, color, material or other canonical API field is added.
No CMS import/upload, WooCommerce mutation or production activation is included.
