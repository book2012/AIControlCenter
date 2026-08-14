# PA-02 OpenClaw Adapter v1

Status after Git closeout: closed at milestone
`OPENCLAW_ADAPTER_V1_VALIDATED`.

## Decision

AIControlCenter consumes optional, replaceable OpenClaw capability through the vendor-neutral
`CapabilityObserver` contract. `CapabilityStatusService` is the application
facade. The replaceable `integrations.openclaw.OpenClawAdapter` normalizes only
configuration and read-only health/readiness observations.

The dependency direction is:

`ops.macos.runtime.application → integrations.openclaw → core.capabilities`

OpenClaw-specific details do not enter generic core policy. Core imports neither
`ops.*` nor `integrations.*`; macOS outer composition injects the adapter into
`core.api.create_app`. Platform-neutral `create_app` performs no OpenClaw
discovery and fails closed with value-free `UNAVAILABLE` evidence when no
adapter is injected. macOS composition truthfully projects `NOT_DEPLOYED` from
the validated manifest. OpenClaw is not a Control Plane: AIControlCenter retains
business logic, governance, Production authorization, deployment control,
workflow policy, infrastructure mutation authority, audit, and
business/customer state.

## Truthful deployment decision

The canonical manifest is schema-validated before its unique OpenClaw entry is
trusted. That entry has
`required=false`, `production_status=NOT_DEPLOYED`, unassigned runtime and
supervisor, no endpoint, and `runtime_health=false`. Local read-only discovery
found no OpenClaw executable, named application/config path, or launchd label.
No trustworthy launchd, runtime, or Service Platform identity is proven.
Consequently PA-02 retains `NOT_DEPLOYED`, does not invent a lifecycle identity,
adds no `service_platform` lifecycle definition, and does not change aggregate
Runtime Health.

## Contract and safety

The `1.0` JSON projection contains provider/service identity, status,
availability, health/readiness, proven adapter capabilities, value-free
tri-state configuration/authentication evidence, optional explicitly observed
runtime kind, bounded evidence, a
value-free error type, and explicit governance flags. Status is one of
`AVAILABLE`, `UNAVAILABLE`, `NOT_CONFIGURED`, `NOT_DEPLOYED`, or `DEGRADED`.
Malformed and indeterminate observations fail closed.

The only API surface is `GET /api/capabilities/openclaw`. No
POST/PUT/PATCH/DELETE capability implementation exists. PA-02 provides no
prompt forwarding, tool/action execution, lifecycle execution, Production
authorization, deployment operation, `launchctl` operation, infrastructure
mutation, or customer/business state. OpenClaw observations can never authorize
an AIControlCenter operation.

Endpoint, authentication, transport, and runtime identity are currently
`UNKNOWN`/unproven by default. The implementation uses no `OPENCLAW_ENDPOINT`
or `OPENCLAW_API_KEY` convention. Secret/config evidence is value-free: no
endpoint URL, key, token, cookie, header, environment value, credential value,
or exception message is projected. Missing, duplicate, or malformed manifest
identity fails closed.

## Validation and closeout

Focused PA-02 validation passed 79 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-02 canonical invocation. `git diff --check`
passed. No Production mutation occurred, and no additional deployment,
`launchctl`, `runtime/current`, credential, or live-service operation occurred.
No Notion synchronization is claimed. PA-01 and OPS-01B remain closed and
unchanged. WordPress and unrelated Shadow maintenance remain separate future
work.
