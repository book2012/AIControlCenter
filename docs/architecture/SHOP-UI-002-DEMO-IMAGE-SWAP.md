# SHOP_UI_002 — repository-local demo image swap plan

**Historical baseline, superseded by SHOP_MEDIA_001.** The current inventory is
`brands/orange-coco/assets/media/SHOP_MEDIA_001.json`: **7 / 92 product photos
replaced, 85 pending**, plus a new brand-owned boutique hero. The old JSON file
beside this document remains the pre-swap checksum baseline. See
[current media ownership and procedure](../../brands/orange-coco/assets/media/README.md).
The former shared product/hero mapping described below is no longer active.

Status: **PENDING_BINARY_REPLACEMENT**. Replaced: **0 / 92**. This is the
explicitly permitted plan fallback, not a completed photo replacement.

The existing catalog contains 92 independently sourced sample photographs.
There is no complete, product-matched replacement set in this workspace, and
browser visual QA is unavailable in this environment. A consistent replacement
batch and crop review remain separate work. No image was generated, downloaded,
relabeled as a replacement, or copied over an existing JPEG in this pass.

## Exact inventory

[SHOP-UI-002-DEMO-IMAGE-SWAP.json](SHOP-UI-002-DEMO-IMAGE-SWAP.json) enumerates
every pending file individually: product ID, canonical name and description,
exact repository target, candidate destination, unchanged photo URL, current
SHA-256, framing brief, and pending status. Coverage: 20 tops, 20 dresses,
15 bottoms, 15 outerwear, 12 bags, 10 accessories. The focused tests compare
this plan with the actual catalog, filenames and all 92 current checksums.

The root remains:

`deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products/`

The public presentation path remains:

`/homepage/assets/storefront/photos/{category}/{product_id}.jpg`

The compact home hero reuses `products/top/oc-demo-top-0001.jpg`. Its replacement
therefore changes the hero as well as cards and PDP; review its wide crop too.
Historical demo assets outside the active 92-product catalog are not consumed
by these Homepage routes and are outside this plan.

## Replacement procedure (local assets only)

1. Prepare one candidate for each exact `candidate_path` in the JSON inventory.
   Use a coherent international fashion-model editorial direction with adult
   fictional models for generated images, or licensed adult-model photography
   with recorded provenance. Do not infer a real person's nationality from
   appearance. No celebrity likenesses, branded campaign imitations or logos.
2. Follow the shared brief and the per-product canonical name/description.
   Do not use noncanonical catalog gallery, size, color or material fields to
   invent PDP claims. Bags/accessories should stay prominent in model photos.
3. Review all candidates for garment correspondence, consistency, natural
   anatomy, clear accessories, and the 2:3 card/PDP crop. Review home at 320/390px,
   tablet at 768px and desktop at 1440px, including the compact hero crop.
4. Save real JPEG files under the existing exact target filenames. Copy only
   selected candidates into repository targets after visual review. Do not
   change product IDs, catalog paths, adapter mappings or canonical schemas.
5. Update the corresponding entries in
   `deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/asset-manifest.json`:
   actual source/provenance, dimensions, descriptive alt and new SHA-256.
   Generated assets must record generation provenance/prompt rather than
   retaining the old Pexels photographer/photo attribution. Retain the old
   provenance in repository history; do not misattribute replacement images.
6. Update this inventory's statuses and counts truthfully. Run the focused
   storefront tests, read-only Shopping regressions, photo route byte checks,
   browser visual QA where available, and `git diff --check`.

This procedure contains no CMS upload/import, WooCommerce mutation, deployment,
runtime activation, staging, commit or push. Those actions are not authorized.
