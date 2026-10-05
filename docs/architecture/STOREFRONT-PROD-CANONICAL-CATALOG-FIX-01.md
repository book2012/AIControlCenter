# STOREFRONT-PROD-CANONICAL-CATALOG-FIX-01

## Problem

PROD activation of the immutable 0.19.0 storefront proved that the plugin artifact, Colima VM view, and container view were identical, but the public product feed remained empty. The canonical Shopping API returned five valid production catalog items with `source=mock`; the renderer discarded every non-`demo` item before card rendering.

## Contract correction

The production promotion contract preserves canonical Shopping data. The presentation adapter may map approved demo product IDs to packaged agachichi media, but lack of a media match must degrade to the existing neutral image fallback rather than remove the product. The renderer therefore keeps every array-shaped canonical catalog item and leaves media eligibility to `AI_Shopping_Agachichi_Presentation_Adapter::image_url()`.

## Versioning and boundaries

This is a patch candidate version `0.19.1`. The immutable 0.19.0 release remains unchanged for audit and rollback. This source change does not alter the canonical API, database, Caddy, Colima, WordPress runtime, or production release by itself. A new exact candidate commit, acceptance update, immutable materialization, and explicit production activation are required before 0.19.1 can reach PROD.

## Accepted payload identity

The exact 0.19.1 payload candidate is `ee229261459e24d1a2d73b39bbbb8e2fa4042ba9`. Acceptance binds this exact commit while preserving the previous immutable 0.19.0 release as rollback evidence.
## Production activation evidence

The accepted `0.19.1` payload `ee229261459e24d1a2d73b39bbbb8e2fa4042ba9` was materialized under `~/AIControlCenterRuntime/releases/storefront-prod` while preserving the prior immutable `0.19.0` release. The materializer was hardened to support successive immutable promotions: an existing current release is verified and preserved, a new commit-addressed release is added, `current.json` is switched atomically, and a failed post-write validation restores the prior current marker and removes only the failed new release. Focused materialization/runtime/promotion validation passed with 48 tests.

PROD activation recreated only `shopping-wordpress`. The container remained on the same image digest, its complete environment matched the pre-activation environment, and the storefront bind is read-only at the exact 0.19.1 release path. `shopping-db` remained the same healthy container, Caddy PID remained unchanged, and all three preview containers retained their identities and healthy state.

Host, Colima VM, and WordPress container SHA-256 values for `ai-shopping-storefront.php` are identical. The runtime reports plugin version `0.19.1`, recent WordPress logs contain no fatal-error signal, and the public homepage exposes exactly five unique canonical product links (`mock-001` through `mock-005`). Homepage, product detail, category, search, storefront CSS, and storefront JavaScript checks all returned HTTP 2xx; the CSS and JS asset URLs are versioned `0.19.1`.

Browser visual QA is PASS using Google Chrome 154. Desktop and mobile Home/PDP renders were captured successfully. A DevTools browser session performed real anchor clicks from Home to `mock-001` PDP, browser history Back to Home, the `women-tops` category filter, and the Search link. The PDP rendered `AI Home Datacenter Starter Guide` with the product-inquiry section; Search rendered its form. At the mobile breakpoint the browser reported `document.documentElement.scrollWidth == window.innerWidth` on Home, PDP, and Category, so no horizontal document overflow was observed. This closes the Storefront 0.19.1 operational sprint.
