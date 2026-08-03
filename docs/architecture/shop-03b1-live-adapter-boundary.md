# SHOP-03B1 live adapter boundary

Authorization is user-attested for SHOP-03B at `2026-08-03T08:54:00+09:00`, but does not bind an exact product, ProductDraft revision, deployment intent, or live timestamp.

The boundary consumes only an immutable, digest-verified SHOP-03A `ControlledWritePlan`. ProductDraft v1.0.0 fields are translated through an explicit allowlist into a canonical update body; the target identifier is bound in `/wp-json/wc/v3/products/{id}`. The only supported operation is `UPDATE_PRODUCT`.

The credential provider is constructor-injected, returns a redacted credential only at call time, and defaults to unavailable. The synchronous transport receives immutable safe metadata, the credential separately, and a bounded timeout. It also defaults to unavailable. There is no network implementation, retry, compensating write, storage, or API route.

Intercepted responses are normalized to an immutable allowlisted result and deterministically reconciled. Every preview/result states `mode: INTERCEPTED_VALIDATION` and `live_write_performed: false`. External requests: 0. WooCommerce writes: 0. Production activation: `NOT_AUTHORIZED`.
