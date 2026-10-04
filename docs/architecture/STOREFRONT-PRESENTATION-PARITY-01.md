# STOREFRONT-PRESENTATION-PARITY-01

This document records the isolated WordPress presentation candidate. It is a
source candidate only; it is not a production acceptance or activation record.

## Comparison basis

- Base Control Plane commit: `29a40dc6f22b2b436a91c08532cb61387dc6d634`
- Canonical DEV accepted release: `08a0ac44952c964e594c1dd12d83769a1336d27f`
- Original WordPress presentation candidate: `567cb90ee7fdec0fa82f39c3ad6ce28d46381479`
- Candidate plugin version: `0.19.0`
- Presentation identifier: `SHOP_MEDIA_003_AGACHICHI`
- Original audit: `CRITICAL_GAPS=6`, `MAJOR_GAPS=12`, `MINOR_GAPS=3`, `MATCH_ITEMS=4`

The DEV source contract is the unified agachichi storefront in
`core/homepage/storefront.py`, `core/homepage/ui/storefront.html`,
`core/homepage/ui/storefront-search.html`,
`core/homepage/ui/storefront-product.html`,
`core/homepage/ui/storefront-card.html`, `core/homepage/ui/storefront.css`,
and `core/homepage/ui/storefront.js` at the canonical DEV commit.

## Resolved gap matrix

| Severity | Gap | Resolution in this candidate | Source paths |
| --- | --- | --- | --- |
| Critical | C1 global page structure | WordPress front page and PDP now use the DEV header, main, footer, and semantic view structure. | `templates/storefront-front-page.php`, `templates/product-detail.php`, `includes/class-renderer.php` |
| Critical | C2 header contract | Restored the DEV wordmark, search affordance, preview notice, spacing, and labels; removed account/bag-only header behavior. | `templates/storefront-front-page.php`, `assets/agachichi-v1.css` |
| Critical | C3 primary navigation | Restored the DEV feed filter rail and category navigation semantics, including active state and mobile ordering. | `includes/class-renderer.php`, `assets/agachichi-v1.css` |
| Critical | C4 homepage sections/order | Homepage now renders hero, filter rail, feed heading/count, feed/status, product grid, browse links in DEV order. | `includes/class-renderer.php` |
| Critical | C5 search/category behavior | Search and category state are server-rendered from the adapter, with persisted query/category values and DEV empty/error copy. | `includes/class-shortcodes.php`, `includes/class-renderer.php` |
| Critical | C6 product detail behavior | PDP now matches DEV metadata, image/fallback, availability, variants, inquiry, notice, description, and back affordance. | `includes/renderers/class-product-detail-renderer.php`, `templates/product-detail.php` |
| Major | M1 hero presentation | Uses the packaged agachichi hero mapping with DEV hero markup, alt text, dimensions, and object-fit behavior. | `includes/class-renderer.php`, `includes/class-presentation-adapter.php`, `assets/agachichi-v1.css` |
| Major | M2 section typography | Migrated DEV type scale, line heights, weights, letter spacing, and Korean word-breaking rules. | `assets/agachichi-v1.css` |
| Major | M3 spacing/layout | Migrated DEV max widths, gutters, collection spacing, feed spacing, and detail grid. | `assets/agachichi-v1.css` |
| Major | M4 color treatment | Migrated DEV ivory/paper/orange/accent/ink/muted/line palette. | `assets/agachichi-v1.css` |
| Major | M5 borders/shadows/focus | Migrated DEV border, background, focus-visible, button, and hover treatment. | `assets/agachichi-v1.css` |
| Major | M6 product card markup | Product cards are DEV `li.product-card`/`product-link`/`product-photo`/`product-caption` structures with semantic labels. | `includes/class-renderer.php` |
| Major | M7 image sizing/aspect ratio | Product images use DEV 800×1200 attributes and 2:3 object-fit presentation; fallback remains available. | `includes/class-renderer.php`, `includes/renderers/class-product-detail-renderer.php`, `assets/agachichi-v1.css` |
| Major | M8 category result layout | Search results use DEV collection heading, category nav, conditions, feedback, grid, and pagination structure. | `includes/class-renderer.php` |
| Major | M9 search control | Search input, hidden category state, suggestions, context copy, and clear action match the DEV contract. | `includes/class-renderer.php` |
| Major | M10 query persistence | WordPress query names are adapted to routing while preserving `q`, category, and page state in rendered controls and links. | `includes/class-shortcodes.php`, `includes/class-renderer.php` |
| Major | M11 pagination/page 2 | Previous/next links preserve category and query state and expose the DEV page label and page-2 behavior. | `includes/class-renderer.php` |
| Major | M12 detail metadata/description | Category, price/currency, stock label, variants, inquiry, description fallback, and media fallback use DEV labels and hierarchy. | `includes/renderers/class-product-detail-renderer.php` |
| Minor | m1 copy/messaging | Removed candidate-only English merchandising copy, static color options, fake related products, account/bag links, and alternate CTA wording. | `templates/storefront-front-page.php`, `includes/renderers/class-product-detail-renderer.php` |
| Minor | m2 route/back semantics | WordPress routes may differ, but product links carry `return_to`, validate same-origin navigation, and preserve the originating home/list state. | `includes/class-renderer.php`, `includes/renderers/class-product-detail-renderer.php` |
| Minor | m3 responsive/navigation details | Migrated the DEV 900px/600px breakpoints, mobile 2-column cards, horizontal categories, and explicit filter-rail mobile placement. | `assets/agachichi-v1.css` |

## Architecture boundaries

- AIControlCenter remains the sole Control Plane and the source of catalog
  behavior and commerce data.
- WordPress is a read-only CMS/presentation adapter. Its renderer projects
  validated API responses and does not own catalog, pricing, inventory, or
  checkout policy.
- WooCommerce remains the Commerce Engine. This candidate does not write
  WordPress options, WooCommerce state, or a database.
- Shopping API calls remain server-side through `AI_Shopping_API_Client`.
  The browser script contains no API base URL, Woo credentials, or internal
  authorization material.
- The host Caddy/public security topology is unchanged. No lifecycle command,
  runtime activation, or production payload was changed.
- The accepted agachichi media manifest and packaged media are preserved;
  `SHOP_MEDIA_003_AGACHICHI` remains the mapping identifier.

## Source-parity checks

The focused contract is in
`tests/test_storefront_presentation_parity_01.py`. It covers homepage,
search, category, page 2, PDP, navigation, responsive breakpoints, media
identity, browser-boundary safety, and the public security assumption. The
legacy promotion and public-storefront migration checks remain required.

## Final visual QA required

This candidate still requires isolated visual QA against the accepted DEV
release at desktop, tablet, and mobile widths. Visual QA must confirm hero
crop, real browser font metrics, WordPress theme interaction, image loading,
search/category transitions, page 2, product back behavior, and the inquiry
interaction. Production acceptance constants remain unchanged until that QA
is explicitly accepted.
