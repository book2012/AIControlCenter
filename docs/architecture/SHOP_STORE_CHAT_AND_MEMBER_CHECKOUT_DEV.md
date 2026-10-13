# DEV storefront chat and member checkout

## Chat behavior
- Product detail pages introduce a bounded public summary derived from the current catalog: name, category, price notes, availability, options and description.
- Home, search, cart, orders and checkout pages receive page-specific guidance and suggested prompts. Suggestions fill and submit the request directly; the message composer remains available for a new typed question.
- Opening the chat does not focus the message composer, so mobile keyboards do not appear automatically.
- The chat inquiry API remains product-ID plus message. It resolves current catalog data server-side and rejects client-supplied facts. The page context does not include order PII.

## Checkout presentation
- Checkout shows a LOGIN link before the existing non-member order form. The WordPress DEV login carries a constrained return path to checkout.
- After a WooCommerce login, a DEV-only authenticated WordPress AJAX handler returns the signed-in account's saved recipient, phone and shipping fields. The checkout script fills only empty fields; customers can edit them. Guest access receives no profile fields.
- The non-member form retains SMS verification, delivery review, quote revalidation and explicit final order confirmation.

## Member SMS boundary
Member SMS bypass remains pending. The current Shopping order API authenticates a Shopping customer session whose contact has a server-verifiable phone-verification receipt. WooCommerce login cookies and saved profile values are not that receipt and are not linked to the Shopping customer identity. A browser flag or profile lookup must never bypass API checks.

Before enabling member order without SMS, implement a signed, expiring, audience-bound, replay-protected WooCommerce identity assertion to the Shopping control plane. Bind its Woo customer ID to an existing Shopping customer identity and verified phone; authorize profile reads and order writes server-side; add CSRF, replay, isolation and negative tests. Guests must continue to use the phone-verification flow.

## Account navigation
The storefront signup link uses the normal menu style by default. The DEV account header marks LOGIN active only on the unauthenticated login page and 회원가입 active only on the registration page; inactive links have no underline.

## Scope and state
DEV source changes only. No PROD account or order behavior changed. Branch tests pass, but no immutable DEV release has been activated. Member SMS bypass, live mobile login verification and final DEV activation remain open work.
