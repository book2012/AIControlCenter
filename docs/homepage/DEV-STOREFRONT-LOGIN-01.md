# DEV Storefront Login Link

## Behavior

The shared agachichi Homepage header inserts a LOGIN link immediately after
검색 on storefront, product, search, cart, checkout, and order pages. The
link opens WooCommerce's DEV account page at /my-account/. Its responsive
style keeps the touch target at least 44 pixels high and reduces padding on
small screens.

Customer self-registration remains disabled in the DEV WooCommerce settings.
Guest inquiry and the existing phone-verified order flow remain unchanged.

## DEV routing

The DEV ingress requires its existing Basic Auth and retains noindex headers.

| Request | DEV destination |
| --- | --- |
| / | Rewrite to /homepage/storefront, then Homepage preview on 127.0.0.1:18080 |
| /homepage/*, /shopping/* | Homepage API on 127.0.0.1:18080, except the order routes below |
| /dev-order/*, /shopping/orders/*, /shopping/auth/* | Isolated order service on 127.0.0.1:18445 |
| /my-account/* and remaining WordPress pages | DEV WordPress on 127.0.0.1:55274 |

The DEV WordPress account page resolves to
https://dev.bokstory.duckdns.org/my-account/. Production routing and
WooCommerce data are outside this change.

## Validation

The focused preview suite verifies the shared script inserts LOGIN after the
search action, uses the DEV account path, and loads responsive button styles.
The immutable Homepage DEV release is updated only after tests pass and a clean
commit is available.
