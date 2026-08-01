# SHOP-02A Product Draft Workflow Architecture

Status: architecture complete; runtime, persistence, endpoints, external execution and production writes are not implemented or authorized.

## Decision

AIControlCenter owns the `ProductDraft` aggregate: governance, immutable revision lifecycle, deterministic validation, human decision, authorization and audit references, and deployment intent. A draft is a proposal derived from an immutable WooCommerce snapshot reference or digest; it is never local product truth. WooCommerce remains the product source of truth and Commerce Engine. WordPress remains the CMS Engine. Ubuntu is a stateless infrastructure worker and owns none of this state or logic.

The versioned, offline Draft 2020-12 contracts are registered by `docs/contracts/shopping/product-draft-manifest.json`. The baseline symbol inventory and its measurement method are machine-readable in `docs/contracts/shopping/inventory.json`. Supported proposed fields are name, description, SKU, regular/sale price, inventory quantity, stock status, categories, tags and image references because current product snapshot and management projections evidence them. Variations, attributes, dimensions, shipping, tax, downloadable/virtual settings, linked products, purchase notes, reviews and arbitrary metadata are explicitly deferred.

## Aggregate and provenance

Each revision has stable `draft_id`, unique `revision_id`, monotonically increasing `revision_number`, nullable `previous_revision_id`, UTC creation time, actor and correlation references. Editing creates a new immutable revision and supersedes the old revision. Suggestions identify `HUMAN`, `AI`, `IMPORT` or `SYSTEM` provenance. AI suggestions may carry non-secret provider/model and generation-audit references. Raw prompts and credentials are forbidden. Suggestion provenance grants no approval.

Validation is deterministic over a canonical input digest and records errors, warnings, validator version and UTC validation time. A human decision names the exact reviewed `revision_id`; the reviewer type is structurally fixed to `HUMAN`. AI and service actors cannot approve. New or rejected revisions must be validated and reviewed independently; approvals never transfer. Revocation permanently invalidates the approval reference.

## Closed lifecycle

The complete permitted transition set is:

- `DRAFT → VALIDATED`; `VALIDATED → DRAFT`; `VALIDATED → REVIEW_REQUIRED`.
- `REVIEW_REQUIRED → APPROVED`; `REVIEW_REQUIRED → REJECTED`.
- `APPROVED → REVOKED`; `APPROVED → SUPERSEDED`; `APPROVED → DEPLOYMENT_READY`.
- `DRAFT|VALIDATED|REVIEW_REQUIRED|REJECTED|REVOKED → SUPERSEDED` when a replacement revision is created.
- `DEPLOYMENT_READY → REVOKED`; `DEPLOYMENT_READY → SUPERSEDED`.

Every unspecified transition is rejected. There is deliberately no `DEPLOYED` state. `DEPLOYMENT_READY` says only that architecture prerequisites are referenced; it does not authorize or prove an external write.

Every command requires actor, correlation, audit, idempotency, expected `revision_id`, and expected revision-number references plus a timezone-aware UTC timestamp. Optimistic concurrency rejects either stale identity or version. The first accepted idempotency key binds to the canonical command digest and deterministic result digest; an identical replay returns `IDEMPOTENT_REPLAY`, while reuse with different input returns `REJECTED_IDEMPOTENCY_KEY_REUSE` and is audited. Transitions are pure Control Plane decisions and never call WooCommerce.

## Deployment boundary

A deployment intent binds the approved revision, target adapter reference, expected WooCommerce source digest, idempotency key, separate authorization reference and audit reference. It contains no credentials. Creating intent is not execution. External authorization, conflict re-check, adapter write, rollback and reconciliation belong to future separately authorized work.

## Future API design

All of the following are `NOT_IMPLEMENTED` and `NOT_AUTHORIZED`: `POST /shopping/product-drafts`, `POST /shopping/product-drafts/{draft_id}/revisions`, `POST /shopping/product-drafts/{draft_id}/revisions/{revision_id}/validate`, `POST .../review`, `POST .../decision`, `POST .../revoke`, and `POST .../deployment-intents`. Future commands accept the transition contract, require authentication and authorization, and return deterministic conflict/idempotency outcomes. No route is added by SHOP-02A.
