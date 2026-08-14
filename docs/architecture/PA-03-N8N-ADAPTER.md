# PA-03 — n8n Control Plane Adapter v1

Status after Git closeout: `N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`; PA-03 is
validated and closed.

## Boundary and dependency direction

AIControlCenter remains the sole Control Plane. n8n is a replaceable external
automation capability, not the AIControlCenter Control Plane. AIControlCenter
retains business logic, workflow policy, orchestration policy, Production
authorization, governance, audit, deployment control, infrastructure mutation
authority, and business/customer state.

The dependency direction is `ops.macos.runtime.application` →
`integrations.n8n` → `core.capabilities`, with dependency injection into
`core.api.create_app`. Core imports neither `ops.*` nor `integrations.*`.
Existing `core.capabilities` contracts and `CapabilityStatusService` are reused;
no second capability framework exists.

Platform-neutral `create_app` performs no n8n discovery and fails closed with
value-free `UNAVAILABLE` evidence when no adapter is injected. macOS outer
application composition injects the n8n adapter and truthfully projects
`NOT_DEPLOYED`.

The adapter is observation-only. It cannot execute workflows, enable or disable
workflows, create credentials or webhooks, change schedules, mutate
infrastructure, authorize Production, or own platform-wide business policy.

## Evidence and current state

The canonical manifest and schema are validated before the unique n8n identity
is trusted. Current canonical truth is optional, `NOT_DEPLOYED`,
`runtime_health=false`, `runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`.
No sufficiently proven executable, lifecycle, log, or runtime identity exists.
Therefore no PA-01 `service_platform` lifecycle definition was added, and the
optional service remains outside aggregate Runtime Health.

Configuration, authentication, runtime, and transport remain `UNKNOWN` unless
explicitly injected as evidence. No invented n8n endpoint, environment, or
authentication convention is used by the implementation.

## API and data safety

`GET /api/capabilities/n8n` is the only n8n API projection added in PA-03 v1
and returns the shared capability schema. No POST/PUT/PATCH/DELETE capability
implementation exists. There is no workflow execution, workflow enable/disable,
webhook creation, credential creation, schedule mutation, Production
authorization, or infrastructure mutation.

Secret/config evidence is value-free. URLs, API keys, tokens, cookies, headers,
webhook secrets, environment values, configuration contents, and exception
messages are not projected. Shared governance explicitly states
`platform_business_policy_ownership=false` for external capabilities; PA-02
OpenClaw remains compatible.

## Final validation and closeout

Focused PA-03 validation passed 96 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-03 canonical invocation. `git diff
--check` passed.

No Production mutation occurred. No n8n workflow, credential, Docker, launchd,
`runtime/current`, or live-service operation occurred. No Notion
synchronization is claimed. OPS-01B, PA-01, and PA-02 remain closed and
unchanged.
