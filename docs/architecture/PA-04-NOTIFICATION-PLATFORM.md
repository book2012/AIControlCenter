# PA-04 Notification Platform v1

Status after Git closeout: **CLOSED — `NOTIFICATION_PLATFORM_V1_VALIDATED`**

PA-04 Notification Platform v1 is validated. It establishes an
AIControlCenter-owned notification domain and read-only provider-readiness
projection. It does not implement, validate, or authorize delivery.

## Ownership and dependency boundaries

AIControlCenter owns notification intent, routing policy, provider selection,
governance, authorization, audit, retry policy, and the future delivery
lifecycle. `core.notifications` is the provider-neutral domain/platform
boundary. `integrations.notifications` contains replaceable, observation-only
provider adapters. External providers own transport capability only, and
`ops.macos.runtime.application` is the outer composition root.

Core imports neither `ops.*` nor `integrations.*` (`CORE_OPS_IMPORT_COUNT=0`,
`CORE_INTEGRATIONS_IMPORT_COUNT=0`). n8n, OpenClaw, WordPress, notification
providers, and Ubuntu do not own platform-wide notification business logic or
Production authorization. Ubuntu owns no application state.

## V1 contracts

- `NotificationIntent`: opaque intent identity, category, recipient reference,
  priority, and requested provider-neutral channels.
- `NotificationRecipient`: opaque `recipient_id` and `recipient_kind`; no address
  or provider credential is projected.
- `ProviderReadiness`: provider identity, explicit readiness state, tri-state
  configuration evidence, availability, claimed channels, observation-only
  marker, and value-free evidence.
- `RoutingDecision`: `NotificationRoutingStatus` planned or blocked policy result. `PLANNED` is not delivery
  authorization and cannot execute an action.

`NotificationProviderStatus` contains only `AVAILABLE`, `UNAVAILABLE`,
`NOT_CONFIGURED`, `NOT_DEPLOYED`, `DEGRADED`, and `UNKNOWN`.
`NotificationRoutingStatus` contains only `PLANNED` and `BLOCKED`. PA-04 v1
defines no delivery lifecycle because delivery execution does not exist.

## Provider registry and current evidence

The registry accepts injected observation-only provider ports. Provider
observations normalize fail-closed. Only a provider explicitly reporting
`AVAILABLE`, `configured=true`, and `available=true` is routable. Malformed,
contradictory, exception-producing, mismatched, duplicate, or otherwise invalid
providers are non-routable.

Provider identities must match `^[a-z0-9][a-z0-9._-]{0,63}$`. Invalid
identities are never echoed and normalize to the literal `UNKNOWN`.

Telegram is the current known reference provider. Canonical Telegram truth is
optional and `NOT_DEPLOYED`; configuration and readiness remain unknown unless
explicitly observed. `DEPLOYED` or `PRODUCTION` alone never proves provider
availability. No environment variable, credential, endpoint, host, port,
authentication, or network convention is inferred.

The pre-existing `GET /notifications` and `POST /notifications` API and its
`core.notification.service` boundary remain unchanged for compatibility. This
legacy mutation surface is **LEGACY / OUTSIDE PA-04 SCOPE**: PA-04 does not call,
wrap, expand, authorize, or depend on it. Deprecation or migration is deferred
to a future, separately governed sprint.

## Capability-manifest consolidation

`core.capabilities.manifest` is the shared narrow canonical service metadata
lookup. It validates the Draft 2020-12 schema itself, validates the manifest,
requires exactly one requested `service_id`, and fails closed on missing,
duplicate, malformed, schema-invalid, invalid-schema, or unreadable input.
OpenClaw and n8n composition reuse this helper while preserving PA-02/PA-03
outward behavior. The helper is not a second `ServiceTopology` or lifecycle
framework.

## API and governance

Only these PA-04 routes exist:

- `GET /api/notifications/platform`
- `GET /api/notifications/providers`

This is the exact new PA-04 API surface. PA-04 adds no POST, PUT, PATCH, or
DELETE action route and exposes no send, retry, transport execution, Production
authorization, or infrastructure mutation operation. The unchanged legacy
`/notifications` API above is not a PA-04 route and is not claimed to be
read-only.
Every projection declares:

```json
{
  "authority": "AICONTROLCENTER",
  "read_only": true,
  "production_authorization": false,
  "provider_transport_only": true,
  "external_business_policy_ownership": false,
  "action_execution": false,
  "automatic_retry": false
}
```

Provider identities are value-free, bounded to 64 characters, and must match
`^[a-z0-9][a-z0-9._-]{0,63}$`; invalid or mismatched identities fail closed as
literal `UNKNOWN` and are never routable. Evidence and errors contain bounded
types and states only. SMTP credentials,
API keys, bot tokens, webhook secrets, recipient addresses, environment values,
configuration contents, authorization headers, cookies, and exception messages
are forbidden from projections.

## Final validation and safety record

Final exact-code focused validation passed 85 tests after provider identity
hardening. Canonical deployment regression passed with `RC=0` on exactly one
PA-04 canonical invocation. `git diff --check` passed.

No Production mutation occurred. No Production notification was sent. No
external provider I/O or PA-04 notification execution occurred. Legacy
`POST /notifications` was exercised only through TestClient compatibility
tests. No launchd, Docker, `runtime/current`, credential, Caddy, WordPress,
Ubuntu, or live-provider mutation occurred. No Notion synchronization is
claimed. OPS-01B, PA-01, PA-02, and PA-03 remain closed and unchanged.

PA-04 is marked closed after Git closeout at milestone
`NOTIFICATION_PLATFORM_V1_VALIDATED`.
