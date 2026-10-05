# STOREFRONT-PROD-CANONICAL-CATALOG-FIX-01

## Problem

PROD activation of the immutable 0.19.0 storefront proved that the plugin artifact, Colima VM view, and container view were identical, but the public product feed remained empty. The canonical Shopping API returned five valid production catalog items with `source=mock`; the renderer discarded every non-`demo` item before card rendering.

## Contract correction

The production promotion contract preserves canonical Shopping data. The presentation adapter may map approved demo product IDs to packaged agachichi media, but lack of a media match must degrade to the existing neutral image fallback rather than remove the product. The renderer therefore keeps every array-shaped canonical catalog item and leaves media eligibility to `AI_Shopping_Agachichi_Presentation_Adapter::image_url()`.

## Versioning and boundaries

This is a patch candidate version `0.19.1`. The immutable 0.19.0 release remains unchanged for audit and rollback. This source change does not alter the canonical API, database, Caddy, Colima, WordPress runtime, or production release by itself. A new exact candidate commit, acceptance update, immutable materialization, and explicit production activation are required before 0.19.1 can reach PROD.

## Accepted payload identity

The exact 0.19.1 payload candidate is `ee229261459e24d1a2d73b39bbbb8e2fa4042ba9`. Acceptance binds this exact commit while preserving the previous immutable 0.19.0 release as rollback evidence.
