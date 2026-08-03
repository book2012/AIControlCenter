# UI-02 Product Management Console

UI-02 adds the internal presentation route `GET /homepage/product-management`.
It is a responsive, keyboard-accessible, read-only ProductDraft console served
from package-local HTML, CSS, and JavaScript. The document and asset routes are
excluded from OpenAPI; `/homepage/status` remains documented.

## Data boundary

The browser uses only these same-origin reads:

- `GET /shopping/product-drafts?page=1&page_size=100`
- `GET /shopping/product-drafts/{draft_id}`
- `GET /shopping/product-drafts/{draft_id}/revisions/{revision_id}`

The collection is bounded to 100 immutable revisions. Filtering and draft
grouping operate only on that already fetched page. Detail reads use the exact
existing flattened ProductDraft revision response. Deployment preview appears
only when `deployment_intent` is returned. JavaScript owns presentation only;
ProductDraft lifecycle, validation, review, authorization, policy, and audit
logic remain in AIControlCenter.

## State and safety semantics

`AVAILABLE` means the read completed. `EMPTY` means an available collection
returned no items; it is never inferred from a failed read. `UNAVAILABLE` means
the source could not be read, while `DEGRADED` marks reduced console readiness.
`READ_ONLY`, `REVIEW_REQUIRED`, `APPROVED`, and `REJECTED` expose existing API
state. `NOT_AUTHORIZED` is the deployment/write posture.

Requests use an eight-second timeout and safe retry. Rendering uses DOM text
APIs, not remote-data `innerHTML`. There is no browser persistence, external
request, direct WooCommerce call, mutation method, credential handling,
approval/rejection control, or deployment control.

The console is internal only. It adds no public Caddy exposure, authentication
change, production activation, Ubuntu change, or persistent profile. Production
writes remain `NOT_AUTHORIZED`.

Next: `OPS-01_STAGING_CADDY_AUTH_MONITORING`.
