# Orange Coco Shopping Storefront

## Current Milestone

`SHOP-STOREFRONT-S01`

Fashion Homepage v1 presentation is complete.

The public storefront is:

`https://bokstory.duckdns.org/`

Live validation confirmed HTTP 200 and successful rendering of the Orange Coco
presentation shell and AI Style Preview.

## Architecture Ownership

AIControlCenter remains the single Control Plane.

WordPress owns CMS and storefront presentation responsibilities only.
WooCommerce remains the Commerce Engine and catalog truth.
Shopping business logic, policy, orchestration, authorization, AI workflows,
recommendations, and automation remain AIControlCenter-owned.

Ubuntu has no Shopping business logic or application-state ownership.

## Presentation Architecture

The storefront plugin is located at:

`deploy/shopping/wordpress/plugins/ai-shopping-storefront`

The front page is server rendered.

`templates/storefront-front-page.php` owns the page shell, including:

- Orange Coco header
- navigation
- account and bag links
- main storefront shortcode
- minimal footer

`includes/class-renderer.php` owns storefront composition, including:

- hero
- category presentation
- AI Style Preview
- search results
- homepage product sections
- featured products
- product cards

`assets/orange-coco-v6.css` is the active S01 presentation layer.

`assets/storefront-ui.js` is not responsible for generating the application
shell or owning Shopping business composition.

## Fashion Taxonomy

The storefront is women-focused.

Structural presentation categories are:

- TOPS — `women-tops`
- BOTTOMS — `women-bottoms`
- DRESSES — `women-dresses`
- OUTERWEAR — `women-outer`
- ACCESSORIES — `women-accessories`
- MEN — `men`

MEN is intentionally one structural category.

NEW is a merchandising/state view rather than a category-generation ownership
boundary.

## AI Style Preview

AI Style Preview is an editorial/presentation layer.

It is intentionally independent of Shopping API availability.

Current live validation confirmed:

- `AI STYLE PREVIEW` rendered
- `orange-coco-ai-preview` rendered
- demo asset references rendered
- women-focused category links rendered
- MEN category link rendered

Demo images under the plugin assets are presentation/demo assets only.
They are not authoritative product records and do not replace WooCommerce
catalog truth.

## Commerce Failure Boundary

The storefront fails closed for commerce data.

Current live validation confirmed that the presentation layer remains available
while the commerce notice is rendered and API-backed category/product sections
remain unavailable.

Current unresolved work item:

`SHOP-API-READ-001`

The currently persisted WordPress API option is:

`http://host.docker.internal:8000`

This value is recorded as an unresolved runtime configuration, not as the
desired production architecture.

Do not work around the issue by routing production WordPress directly to the
shadow API or by simply switching to a canonical endpoint that is still serving
a mock catalog.

The correct production sequence is:

1. Governed canonical WooCommerce read-only activation.
2. Prove the canonical Shopping API reports the WooCommerce-backed source.
3. Validate categories and featured/product reads.
4. Align the WordPress Shopping API base through the governed configuration
   path.
5. Revalidate live category and product rendering.

## Cache

WordPress transient cache is a short presentation cache only.

The current default lifetime is 30 seconds.

Business state is not stored in WordPress.

## Bootstrap Contract

The commerce bootstrap distinguishes:

- `ai-shopping-storefront` plugin
- `storefront` WordPress theme

The bootstrap fails closed if the bind-mounted Shopping Storefront plugin is
missing and verifies that both WooCommerce and the Shopping Storefront plugin
are active.

## Status

`SHOP_STOREFRONT_S01_PRESENTATION=CLOSED`

`FASHION_HOMEPAGE_V1=CLOSED`

`AI_STYLE_PREVIEW_LIVE=PASS`

`SHOP_API_READ_001=OPEN`

`WOOCOMMERCE_CATALOG_TRUTH=PRESERVED`

`PRODUCTION_SHOPPING_WRITE_AUTHORIZED=NO`
