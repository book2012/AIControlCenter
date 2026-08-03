# UI-01 Internal Shopping Homepage

UI-01 delivers the first browser Homepage at `GET /homepage`. It is an
internal, responsive, presentation-only operator surface served by the
existing Homepage router. Package-local HTML, CSS, and JavaScript use no
frontend framework, npm toolchain, external assets, fonts, or images.

## Read boundary

The browser consumes exactly one same-origin JSON endpoint:

- `GET /dashboard`

The projection keys used are exactly `shopping_management` and
`product_draft_review`. The UI does not call the available Shopping or
ProductDraft detail routes because the Dashboard supplies the bounded summary
required by this view. Requests are GET-only, use an eight-second timeout, and
offer an explicit safe retry. Available empty sources are shown as `EMPTY`;
failed or absent sources are shown as `UNAVAILABLE` and never as zero inventory.

The existing `GET /homepage/status` contract is preserved. Homepage package
assets are served by GET-only routes under `/homepage/assets/`.

The browser document and package-local asset routes are presentation surfaces and are intentionally excluded from OpenAPI. `GET /homepage/status` remains the Homepage API contract.

## Inventory

- Homepage package: `core/homepage/`; router:
  `core/api/routes/homepage.py`; existing status route:
  `GET /homepage/status`. The router was already registered by
  `core/api/app.py` before UI-01.
- Dashboard route: `GET /dashboard`. Its existing response includes the base
  platform projection and failure-isolated optional keys `shopping_management`
  and `product_draft_review`.
- Shopping GET routes: `GET /shopping/health`, `GET /shopping/readiness`,
  `GET /shopping/capabilities`, `GET /shopping/integrations`,
  `GET /shopping/search`, `GET /shopping/featured-products`,
  `GET /shopping/categories`, `GET /shopping/products`, and
  `GET /shopping/products/{product_id}`.
- ProductDraft GET routes: `GET /shopping/product-drafts`,
  `GET /shopping/product-drafts/{draft_id}`, and
  `GET /shopping/product-drafts/{draft_id}/revisions/{revision_id}`.
- Prior Homepage rendering was JSON-only; no HTML, CSS, JavaScript, template,
  static-asset convention, or frontend framework existed in the package.
  UI-01 uses standard-library `importlib.resources` and existing
  FastAPI/Starlette response types. Installed FastAPI, Starlette, and Pydantic
  remain sufficient; no dependency was added.

Only `GET /dashboard` is consumed by the UI. The remaining routes above are an
inventory of available read boundaries, not browser dependencies.

## Release boundary

There is no public Caddy exposure or authentication change in UI-01. There is
no mutation API, active mutation control, direct WooCommerce call, credential,
local application state, or live Commerce write. Production activation remains
`NOT_AUTHORIZED`. ProductDraft and controlled-deployment contracts are
unchanged. Public opening remains pending OPS-01.

Next task: UI-02 Product Management Console.
