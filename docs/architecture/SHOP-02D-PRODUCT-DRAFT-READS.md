# SHOP-02D ProductDraft Read Architecture

AIControlCenter owns the ProductDraft read source port, deterministic query service, review queue, and Dashboard projection. The three resources are:

- `GET /shopping/product-drafts`
- `GET /shopping/product-drafts/{draft_id}`
- `GET /shopping/product-drafts/{draft_id}/revisions/{revision_id}`

The `product_draft_review` Dashboard section is `READ_ONLY`, reports no mutation capabilities, and is failure-isolated. A missing production source yields `UNAVAILABLE`; an injected available source with no snapshots yields zero results. The in-memory adapter is isolated, non-persistent, and intended only for tests/non-production development.

ProductDraft contracts remain 1.0.0. WooCommerce remains published product truth. There are no mutation routes, WooCommerce writes, credentials, external I/O, persistent storage, or production activation. Production writes remain `NOT_AUTHORIZED`. SHOP-03 controlled WooCommerce write architecture is next.
