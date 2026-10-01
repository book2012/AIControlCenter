# SHOP_AI_WOO_ORDER_RUNTIME_V1

This candidate keeps Mac mini / AIControlCenter as the sole control plane and
sole authority for this workflow. It owns the OrderService, orchestration,
authorization boundary, governance and agent tool authority. WooCommerce
remains only the Commerce Engine; WordPress remains only the CMS, and Ubuntu
is not involved.

The live composition is:

`secure read-only configuration → existing WooCommerceReadTransportSession →
existing WooCommerceRESTAdapter → existing canonical WooCommerce commerce read
adapter → WooCommerceExistingStackOrderReadBridge → OrderService`

`READ_ORDER` is enabled. The existing external-read policy and protected
credential-file boundary are reused. The existing transport keeps retries at
zero and redirects disabled, and the composition has no non-GET capability.
Construction does not perform a provider request. The offline composition path
accepts an injected raw read fake and is used by tests.

The canonical Woo `OrderSummary` is projected explicitly into the bounded Order
Core `OrderSnapshot`. The projection keeps Decimal money, requires
timezone-aware timestamps, binds the exact Woo order ID, omits customer contact
data and raw provider JSON, and fails closed for incomplete summaries. The
canonical summary contains no line-item detail, so the Order Core snapshot does
not invent line items.

`LIST_ORDERS` is provider-disabled and fail-closed. No payment, refund,
fulfillment or other commerce mutation is present. A live `READ_ORDER` has not
yet been performed, and production readiness is not declared.
