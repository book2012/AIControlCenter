# SHOP_UI_003_UNIFIED_FEED

The agachichi Home route (`/homepage/storefront`) is a single read-only
editorial feed. The default feed contains all 120 active lookbook products,
mixed across TOP, BOTTOM, OUTER, DRESS, BAG, and ACC in one responsive grid.
The default order round-robins those categories so the opening cards visibly
mix the six editorial groups.

Home renders a bounded 24-card page and exposes a progressive next-page link;
it does not materialize the full catalog in every response. Category pages use
the same existing Shopping pagination/read model. Search keeps its separate
12-card pagination contract.

The filter rail keeps collection and category semantics separate:

- Collections: `ALL`, `HOT`, `SALE`, `UPDATE`, using `collection=`.
- Categories: `TOP`, `BOTTOM`, `OUTER`, `DRESS`, `BAG`, `ACC`, using canonical
  `category=` slugs such as `women-tops` and `women-dresses`.

HOT is empty because there is no explicit HOT membership. SALE is empty because
the current demo data has no canonical sale/discount field. UPDATE uses the
explicit deterministic NEW collection membership. No commercial state is
inferred from feed order or presentation.

Cards remain exactly an image followed by three hashtags. Product names,
prices, categories, availability, descriptions, and future controls remain PDP
concerns. Search remains the dedicated text-search, pagination, and advanced
category route. No canonical schema, Caddy, production, Ubuntu, or WooCommerce
write was changed.
