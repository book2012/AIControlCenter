# PA-05 — WooCommerce Headless Adapter v1

Status: **VALIDATED**

Milestone: `WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`

## Evidence-based deployment truth

The canonical macOS Production service manifest contains no `wordpress`,
`woocommerce`, or commerce database service identity. Repository Compose and
Colima descriptors define a possible local commerce topology, but desired or
deployable configuration is not evidence that it is deployed, configured,
authenticated, running, or API-readable. PA-05 therefore reports WooCommerce
deployment as `UNKNOWN` and fails closed to capability status `UNAVAILABLE`.
Canonical-manifest evidence is emitted only when the validated lookup returns
exactly one WooCommerce service entry; missing, duplicate, malformed,
schema-invalid, and unreadable inputs emit no invented deployment evidence.

No live request, credential lookup, container inspection, database access, or
runtime mutation is part of v1 composition.

## Architecture

AIControlCenter remains the sole Control Plane and owner of shopping business
logic. `core.shopping` is authoritative for the ProductDraft lifecycle,
product policy, workflow, recommendation, customer automation, governance,
and business logic. WordPress remains CMS-only, and WooCommerce remains
commerce-engine-only. `integrations.woocommerce` is a replaceable, read-only
outer adapter in PA-05. `ops.macos.runtime.application` is the outer
composition root. Core imports neither `ops.*` nor `integrations.*`.

The existing historical WooCommerce read transports are not activated by
PA-05. Production catalog readability can become `AVAILABLE` or `DEGRADED`
only from an explicitly injected observer after deployment, configuration, and
authentication evidence are independently proven.

## Read-only API contract

`GET /shopping/providers/woocommerce` returns the shared capability envelope:

```json
{
  "schema_version": "1.0",
  "provider": "woocommerce",
  "service_id": "woocommerce",
  "status": "UNAVAILABLE",
  "available": false,
  "healthy": false,
  "ready": false,
  "capabilities": ["capability.status.read", "commerce.catalog.read", "commerce.product.read"],
  "configuration": {
    "status": "UNKNOWN",
    "configuration_configured": null,
    "authentication_configured": null
  },
  "runtime": {"kind": "UNKNOWN", "transport": "UNKNOWN"},
  "evidence": [],
  "error": {"error_type": "IndeterminateDeploymentStatus"},
  "governance": {
    "authority": "AICONTROLCENTER",
    "read_only": true,
    "production_authorization": false,
    "commerce_engine_only": true,
    "platform_business_policy_ownership": false,
    "infrastructure_mutation": false,
    "action_execution": false,
    "automatic_retry": false
  }
}
```

POST, PUT, PATCH, and DELETE are absent. Evidence and errors are bounded and
value-free; endpoint values, environment values, credentials, headers,
cookies, query secrets, webhook secrets, and exception messages are never
projected.

The adapter exposes no create, update, or delete operation for products,
orders, inventory, customers, or coupons, and no execute, retry, or Production
mutation action.

## Capability governance

`core.capabilities` governance remains AIControlCenter-owned.
`CapabilityGovernanceExtensions` is typed and boolean-only. Integrations
cannot override the reserved governance facts:

- `authority=AICONTROLCENTER`
- `read_only=true`
- `production_authorization=false`
- `infrastructure_mutation=false`
- `platform_business_policy_ownership=false`
- `action_execution=false`

The WooCommerce extension facts are `commerce_engine_only=true` and
`automatic_retry=false`.

Provider-specific unavailable fallbacks are consolidated in the
provider-neutral `UnavailableCapabilityObserver`. Platform-neutral
`create_app` performs no WooCommerce, n8n, or OpenClaw external discovery.
PA-02 OpenClaw and PA-03 n8n outward fail-closed compatibility is preserved.

## Ownership boundary

WooCommerce owns provider-side commerce records and commerce-engine interfaces
only. AIControlCenter retains product policy, ProductDraft lifecycle, AI
generation, recommendations, customer automation, shopping workflow,
analytics, notification policy, support, authorization, governance, audit,
orchestration, and all platform business logic. WordPress remains CMS-only.

## Final validation and safety record

Final focused validation passed 91 tests after the final architecture
correction. Canonical deployment regression passed with `RC=0`, and the PA-05
canonical regression was executed exactly once. `git diff --check` passed.
Import-boundary verification recorded `CORE_OPS_IMPORT_COUNT=0` and
`CORE_INTEGRATIONS_IMPORT_COUNT=0`.

No Production WooCommerce request, WordPress mutation, WooCommerce mutation,
Shopping SQLite mutation, or external commerce I/O occurred. No Docker,
launchd, `runtime/current`, Caddy, Ubuntu, credential, database, plugin, or
theme mutation occurred.

## Next production sprint

`SHOP-CMS-01 — WordPress + WooCommerce Runtime Foundation` will establish the
actual runtime, persistent-state, secret, backup, health/readiness, manifest,
and activation architecture before public storefront exposure. The
WordPress/WooCommerce Production runtime is not claimed as deployed, public
storefront availability is not claimed, and no Notion synchronization is
claimed.
