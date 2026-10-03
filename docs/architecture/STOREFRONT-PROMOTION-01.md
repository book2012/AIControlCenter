# STOREFRONT-PROMOTION-01 — agachichi production promotion candidate

## Status

This document records a candidate build only. It does not claim that the
production storefront has been deployed, activated, or mutated.

The candidate is derived from Git commit
`08a0ac44952c964e594c1dd12d83769a1336d27f` and is identified by the accepted
presentation contract `SHOP_MEDIA_003_AGACHICHI`. Review and a separately
authorized production activation remain required.

## Runtime and ownership boundary

DEV deployment is not PROD promotion. The accepted DEV presentation runs in
the Homepage FastAPI preview; the production candidate runs in the existing
WordPress adapter. DEV FastAPI runtime is not copied into the production
WordPress runtime.

WordPress owns presentation adaptation only: templates, CSS, browser
interaction, plugin-local media mapping, and server-side rendering of data
returned by the canonical Shopping read interface. AIControlCenter remains the
sole Mac mini M4 Control Plane and owns governance, policy, orchestration,
authorization, audit, deployment control, business logic, and commerce
interfaces. No browser-side Shopping API access or business logic was added.

The existing server-side API boundary remains
`http://host.docker.internal:58081`. That address is not emitted into browser
JavaScript or public presentation markup. Existing product detail and search
calls remain server-side through `get_product()` and `search()`; no duplicate
PHP product catalog was introduced.

## Derived media artifact

Media selection is manifest-driven. The deployment manifest at
`assets/agachichi-v1/deployment-manifest.json` is derived from
`brands/agachichi/assets/media/SHOP_MEDIA_003.json`, ordered deterministically,
and records the source relative path, deployed relative path, and SHA-256 for
every packaged file. It contains the approved agachichi hero and the 120
`GENERATED` product assets. Planned or inactive media are not promoted.

The PHP presentation adapter is the single product/media mapping boundary. A
product without a manifest-approved match fails safely to the neutral image
state. Production media is served from the plugin asset namespace, never from
`/homepage/assets/` or a DEV host.

## Data and commerce continuity

The promotion artifact is presentation-only. The production database is not
copied from DEV, and canonical product, order, customer, payment, and refund
data are not replaced by the candidate. WooCommerce orders, customers,
payments, and refunds remain owned by the existing commerce runtime.

No Caddy configuration is changed by this presentation promotion. Host Caddy
remains the only public edge. No live WordPress write, database mutation,
WooCommerce write, service reload, Docker/Colima mutation, or Ubuntu access is
part of this candidate build.

## Rollback and review

The previous Orange Coco CSS, demo assets, and legacy presentation files stay
in Git as rollback assets. The candidate adds the separate `agachichi-v1`
asset namespace and stylesheet and switches enqueue behavior to the agachichi
presentation without deleting the prior assets.

The next step is candidate review. Production activation, if later approved,
must be separately authorized and independently verified.
