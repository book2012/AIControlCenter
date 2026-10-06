# Uploaded-only DEV storefront

Default lookbook preview excludes legacy samples at the catalog adapter boundary before counts, search and pagination. Existing sample files remain archived and accessible to explicit fixture composition (include_samples=True); customer sample product/PDP lookups return 404. New enabled upload records appear without an ID allowlist. Order history and order API are unchanged. Homepage hero remains brand artwork.

Validation: 126 focused regressions passed; seven isolated real Chrome chatbot checks passed with the default uploaded-only factory, no SMS/provider calls. Legacy catalog regressions explicitly opt into samples. Previously stale legacy inquiry tests now exercise their isolated canonical router with access-token checks instead of the intentionally blocked customer preview route.
