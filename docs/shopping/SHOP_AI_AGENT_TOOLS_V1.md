# SHOP_AI_AGENT_TOOLS_V1

AIControlCenter owns the read-only Shopping Tool facade and remains the sole
authority for commerce interpretation and orchestration. The Agent is
interpretation/orchestration only; AIControlCenter is the sole authority for
policy, authorization, provider access and business logic. The structured path
is:

`BrainAgent → AgentActionRouter → ShoppingToolFacade → AIControlCenter service`

The agent can invoke exact structured names:

- `shopping.order.read`
- `shopping.order.status`
- `shopping.product.get`
- `shopping.product.search`

Order tools call `OrderService`. Product tools use the existing
`ShoppingService` interface when injected; otherwise they are explicitly
unavailable read-only capabilities. Tool arguments are validated before service
invocation, unknown names fail closed, registries are deterministic, and
results are bounded JSON-safe projections with no raw provider object.

There is no direct Agent → WooCommerce path and no direct Agent → Ubuntu path.
The agent receives no Woo credentials and has no Woo REST, HTTP client or
credential-loader dependency. These write tools are disabled:

`shopping.order.create`, `shopping.order.update`, `shopping.payment.*`, and
`shopping.refund.*`.

Credential isolation continues to use the established protected read-only
credential file only from the explicit live runtime entrypoint. A live
`READ_ORDER` has not yet been performed, and production readiness is not declared.
