# ACTIVATION-01B Read-Only Activation Inspector Architecture

<!-- AICONTROLCENTER:ACTIVATION_01B_RUNTIME_LAYOUT_FIX:START -->
## ACTIVATION-01B Runtime Layout Correction

Status: `COMPLETE`

Read-only operational validation discovered a Control Plane
observation-path mismatch.

Canonical Runtime layout:

- Runtime environments: `runtime/venvs/<runtime-id>`
- Candidate metadata: `metadata.json`
- Source identity: `.aicontrolcenter-source-commit`

The inspector previously looked under `runtime/releases/<runtime-id>`
and expected `runtime-metadata.json`.

The repair changes observation logic only.

No Runtime environment was created, removed or modified.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_RUNTIME_LAYOUT_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_C4:START -->
## ACTIVATION-01B-C4 Read-Only Inspector

Status: `COMPLETE`

ACTIVATION-01B read-only inspector implementation is complete.

Implemented capabilities:

- Versioned activation inspection policy
- Versioned localhost route manifest
- Existing bounded Git evidence reuse
- Bounded macOS read-only adapters
- Exact `launchctl print` inspection
- Structured `lsof -F` listener inspection
- Runtime filesystem observation
- Isolated Runtime Python `-I -S --version` probe
- Exact localhost HTTP probes
- Immutable pure evaluator
- Launchd serving-target observation
- Canonical `PROCESS_SERVING_TARGET_MATCH` check
- Actual-evidence report materialization
- Evidence digest regeneration
- Check evidence-reference regeneration
- Canonical report digest generation
- Final report JSON Schema validation
- Deterministic CLI exit codes

Status contract:

- `READY_FOR_AUTHORIZATION_REVIEW` -> exit `0`
- `BLOCKED` -> exit `2`
- Invalid policy, manifest or contract -> exit `3`
- Observation or internal error -> exit `4`

Evidence mismatches remain `BLOCKED`.

No exit code grants Production authorization.

C4 focused integration gate: `43 passed`

Base commit: `9f7d71a08235d23502c72c417a029b480b29a5e8`

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`

Implementation milestone:

`ACTIVATION-01B_READ_ONLY_INSPECTOR_IMPLEMENTATION_COMPLETE`

This milestone does not authorize Runtime activation, service restart,
rollback, public opening, Ubuntu mutation or Production.
<!-- AICONTROLCENTER:ACTIVATION_01B_C4:END -->

## Status

Gate:

`ACTIVATION-01B — Architecture Frozen`

This document defines the architecture of a read-only activation inspector.

It does not authorize or perform Runtime activation, service restart,
rollback, launchd modification, Caddy modification, public opening, Ubuntu
modification or Production authorization.

Production remains `NOT_AUTHORIZED`.

## Predecessor binding

ACTIVATION-01B begins after completion of ACTIVATION-01A.

- ACTIVATION-01A closure commit:
  `43975f6e26986fd91c9a715786e7c68deb63f612`
- Candidate Runtime: `acd80ab9f6ae`
- Active Runtime: `b9ad351a7241`
- Canonical serving target: `core.api.shadow:app`
- LaunchDaemon:
  `system/com.aicontrolcenter.api.shadow`
- Listener: `127.0.0.1:18100`
- Production authorization: `NOT_AUTHORIZED`

Canonical predecessor contract:

`docs/operations/macos/ACTIVATION-01A-RUNTIME-ACTIVATION-CONTRACT.md`

## Objective

ACTIVATION-01B determines whether the Mac Control Plane state is eligible
for a future human activation-authorization review.

It does not determine that activation is authorized.

The inspector must:

- Observe bounded local state
- Validate observations against versioned policy
- Produce canonical JSON evidence
- Fail closed on unavailable, malformed or mismatched evidence
- Preserve zero operational mutations
- Keep Ubuntu outside governance and activation authority

## Control Plane boundary

AIControlCenter remains the single Control Plane.

The Mac mini remains the always-on Brain and inspection host.

Ubuntu remains a stateless infrastructure worker and is ineligible for:

- Activation governance
- Authorization
- Application state
- Business logic
- Evidence ownership
- Runtime selection
- Recovery decisions

OpenClaw, n8n, WordPress, WooCommerce, Caddy, APIs and inspected services
cannot issue Production authorization.

## Reused platform capabilities

ACTIVATION-01B must reuse the existing canonical deployment contracts.

Canonical JSON and digest:

- `core.deployment.contracts.canonical_json_bytes`
- `core.deployment.contracts.sha256_digest`

JSON Schema registry and validation:

- `core.deployment.contracts.load_schema_registry`
- `core.deployment.contracts.validate_contract_payload`
- JSON Schema Draft 2020-12

Git evidence:

- `core.deployment.git_readonly_evidence`

Existing design references:

- `core.deployment.operational_bootstrap_preflight`
- `core.deployment.adapters.macos`
- `core.deployment.inspect`
- `ops/macos/runtime/discover-runtime-contract.py`

ACTIVATION-01B must not create another canonical JSON implementation,
digest algorithm or independent schema registry.

## Module architecture

Planned package:

```text
core/deployment/activation_inspector/
├── __init__.py
├── models.py
├── ports.py
├── service.py
├── macos.py
├── runner.py
└── data/v1/
    ├── activation-policy.json
    └── localhost-route-manifest.json
```

Responsibilities:

### models.py

Own immutable inspection requests, observations, checks and reports.

It must not:

- Read files
- Execute subprocesses
- Open sockets
- Read environment variables
- Change host state

### ports.py

Define explicit read-only protocols for:

- Clock
- Git evidence
- Runtime filesystem observation
- Python Runtime observation
- launchd observation
- Process observation
- Listener observation
- Direct-localhost HTTP observation

### service.py

Own deterministic policy evaluation and report construction.

It consumes already collected evidence through ports.

It must not import or call `subprocess`, `socket`, `http.client`, `urllib`,
`os.system` or shell execution functions.

### macos.py

Own bounded Mac adapters.

Every adapter must use:

- Exact argument arrays
- `shell=False`
- Explicit timeouts
- Sanitized errors
- No sudo
- No mutation commands
- No command discovery followed by arbitrary execution

### runner.py

Expose a JSON-first CLI.

Human-readable output may only be derived from the canonical JSON report.

## Versioned policy

Planned policy resource:

`core/deployment/activation_inspector/data/v1/activation-policy.json`

It must bind:

- Schema version
- Policy version
- Exact repository path
- Exact Git branch
- Expected source commit
- Expected current Runtime
- Candidate Runtime
- Runtime root
- Runtime metadata filename
- Source marker filename
- Exact Python executable contract
- Effective `PYTHONPATH` restriction
- Canonical serving target
- Exact launchd domain and label
- Exact application user
- Exact listener host and port
- Process-count restrictions
- Route manifest identity
- Production authorization false
- Ubuntu changes zero

The policy is version controlled and immutable for one inspection run.

Runtime values must not be inferred from newest-file or newest-release
ordering.

## Versioned route manifest

Planned route resource:

`core/deployment/activation_inspector/data/v1/localhost-route-manifest.json`

The manifest must contain an ordered set of exact probes.

Initial required behavior:

- Direct `127.0.0.1:18100` access only
- Declared GET routes expect HTTP `200`
- `POST /health` expects HTTP `405`
- Redirects are failures
- Connection errors are blocking
- Timeouts are blocking
- Public hostnames are prohibited
- Authentication data and cookies are prohibited

Route ordering must be deterministic.

Repository source discovery may support manifest maintenance but cannot
silently add or authorize routes during an inspection.

## Contract schemas

Planned schemas:

```text
core/deployment/contracts/schemas/v1/
├── activation-inspection-policy.schema.json
├── activation-route-manifest.schema.json
└── activation-inspection-report.schema.json
```

The schemas must be registered in:

`core/deployment/contracts/schemas/v1/registry.json`

Planned contract names:

- `ActivationInspectionPolicy`
- `ActivationRouteManifest`
- `ActivationInspectionReport`

All schemas must reject additional properties unless an explicitly bounded
extension point is defined.

Secret-shaped field names must continue to be rejected by the existing
contract validation layer.

## Observation boundaries

### Git

Git evidence must reuse the bounded read-only Git evidence capability.

Required observations:

- Repository path
- Branch
- HEAD
- Clean working-tree status
- Local and configured remote relationship
- Ahead and behind counts
- Exact expected commit relationship

Git evidence is inspection evidence, not authorization.

### Runtime pointer

The inspector may read:

- `runtime/current`
- Symlink type
- Raw link target
- Resolved target
- Runtime directory identity

It must not:

- Create a symlink
- Replace a symlink
- Resolve by newest release
- Repair a broken link
- Select another Runtime

### Runtime metadata

The inspector may read:

- Runtime metadata
- `.aicontrolcenter-source-commit`
- Python executable identity
- Python version
- Dependency identity
- Effective repository coupling

Repository `PYTHONPATH` coupling remains a blocking Production limitation
unless explicitly acknowledged by a future human authorization contract.

### launchd

The only allowed launchd operation is equivalent to:

`launchctl print system/com.aicontrolcenter.api.shadow`

Prohibited launchd operations include:

- `kickstart`
- `bootstrap`
- `bootout`
- `enable`
- `disable`
- `load`
- `unload`
- Plist modification

No fuzzy label search is allowed.

### Process and listener

Listener inspection must bind:

- Address: `127.0.0.1`
- Port: `18100`
- Exact listener PID
- LaunchDaemon application PID
- Expected application user
- Exactly one expected listener

macOS `lsof` field mode may be used as a bounded machine-readable adapter.

Human-formatted table parsing is prohibited when machine-readable field
output is available.

### HTTP

Direct-localhost HTTP inspection must use an exact host and port.

The adapter must not:

- Follow redirects
- Resolve public DNS
- Send credentials
- Send cookies
- Retry automatically
- Change the requested method
- Call any host other than `127.0.0.1`


<!-- AICONTROLCENTER:ACTIVATION_01B_PROBE_HARDENING -->
## Runtime Python probe hardening

The inspector may execute the exact Runtime Python only for one bounded version
identity probe.

The exact argument form is:

    <exact-runtime-python> -I -S --version

The adapter must:

- Use the absolute Python executable path from the inspected Runtime
- Supply arguments as an immutable array
- Use `shell=False`
- Use a bounded timeout
- Ignore inherited `PYTHONPATH` during process execution
- Disable user-site loading
- Prevent bytecode writes
- Use a deterministic sanitized locale
- Capture only bounded standard output and standard error
- Record only sanitized process evidence

The adapter must not:

- Import the application
- Import `core.api.shadow`
- Execute a Python expression
- Execute a Python source file
- Execute `pip`
- Execute `pip freeze`
- Import installed packages to discover versions
- Install or modify dependencies
- Inherit arbitrary environment variables

Dependency identity must be read from finalized Runtime metadata or other
version-controlled dependency evidence.

It must not be discovered by executing arbitrary installed package code.

The effective service `PYTHONPATH` must be observed from bounded launch
configuration and Runtime metadata.

It must not be enabled in the isolated Python version probe.

## Method-denial probe hardening

`POST /health` is an exact method-denial guard probe.

It is not a general POST capability and must never be generalized to another
path or request body.

The probe is allowed only with all of the following bindings:

- Host: `127.0.0.1`
- Port: `18100`
- Method: `POST`
- Path: `/health`
- Request body length: `0`
- Expected response: HTTP `405`
- Attempt count: exactly `1`
- Automatic retry: prohibited
- Redirect following: prohibited
- Authentication headers: prohibited
- Cookies: prohibited
- Authorization headers: prohibited
- User-supplied headers: prohibited
- Public hostname resolution: prohibited

An HTTP status other than `405`, a redirect, timeout, connection failure or
unexpected response framing must produce a blocking result.

The method-denial probe must not authorize a write route, service restart,
Runtime activation, rollback or Production operation.

## Evaluation states

The inspection report uses closed states:

- `READY_FOR_AUTHORIZATION_REVIEW`
- `BLOCKED`
- `ERROR`

`READY_FOR_AUTHORIZATION_REVIEW` means only that observed evidence matched
the versioned inspection policy.

It does not mean:

- Activation approved
- Activation authorized
- Service restart authorized
- Rollback authorized
- Production authorized

Missing or mismatched mandatory evidence yields `BLOCKED`.

Invalid policy, invalid manifest, invalid schema or internal evidence
construction failure yields `ERROR`.

## Evidence report

Every run produces one canonical JSON report.

Required top-level evidence includes:

- `schema_version`
- `inspection_id`
- `inspection_mode`
- `read_only`
- `started_at`
- `completed_at`
- `overall_status`
- `policy_version`
- `policy_digest`
- `route_manifest_version`
- `route_manifest_digest`
- `git`
- `runtime`
- `launchd`
- `process`
- `listener`
- `http`
- `checks`
- `blocking_reasons`
- `warnings`
- `sanitized_errors`
- `production_writes`
- `ubuntu_changes`
- `production_authorized`
- `report_digest`

Every check must include:

- Check ID
- Expected value
- Actual value
- Result
- Blocking severity
- Evidence reference
- Timestamp

The report digest must be calculated from semantic report content before
the `report_digest` field is added.

## CLI contract

Planned invocation:

```text
python -m core.deployment.activation_inspector.runner       --repository /Users/kyouhan/AIControlCenter       --runtime-root       "/Users/kyouhan/Library/Application Support/AIControlCenter/runtime"       --json
```

Planned exit codes:

- `0`: inspection completed with
  `READY_FOR_AUTHORIZATION_REVIEW`
- `2`: inspection completed with `BLOCKED`
- `3`: policy, manifest or contract invalid
- `4`: bounded observation or internal inspection error

No exit code grants authorization.

## Test architecture

Required tests:

- Canonical JSON determinism
- Schema registration and meta-schema validation
- Policy fixture validation
- Route-manifest fixture validation
- Report fixture validation
- Pure service dependency isolation
- Git mismatch fail-closed behavior
- Runtime pointer mismatch
- Broken Runtime pointer
- Runtime metadata mismatch
- Source marker mismatch
- Python executable mismatch
- Repository `PYTHONPATH` limitation
- Exact launchd label allowlist
- Prohibited launchd command rejection
- PID mismatch
- Non-loopback listener rejection
- Multiple-listener rejection
- GET status mismatch
- POST `/health` status mismatch
- Redirect rejection
- Timeout and connection failure
- Deterministic check ordering
- Deterministic report digest
- No secret fields
- No Runtime mutation
- No service restart
- No Ubuntu operation

Real-host verification must remain an explicitly marked integration test.

Default unit tests must use fake ports and fixtures.

## Explicit exclusions

ACTIVATION-01B does not include:

- Runtime activation
- Runtime rollback
- Service restart
- launchd installation
- launchd definition changes
- Caddy changes
- Public opening
- API mutation routes
- Dashboard integration
- n8n workflow activation
- WordPress or WooCommerce integration
- Ubuntu execution
- Production authorization

## Architecture freeze record

- Status: `FROZEN`
- Freeze date: `2026-08-05`
- Predecessor commit:
  `43975f6e26986fd91c9a715786e7c68deb63f612`
- Architecture review: `PASS`
- Runbook review: `PASS`
- Runtime Python probe hardening: `PASS`
- Method-denial probe hardening: `PASS`
- Host command allowlist: `FROZEN`
- HTTP boundary: `FROZEN`
- CLI status semantics: `FROZEN`
- No-mutation test strategy: `FROZEN`
- Runtime mutation count: `0`
- Service restart count: `0`
- Ubuntu modification count: `0`
- Production authorization: `NOT_AUTHORIZED`

This freeze authorizes implementation of read-only contracts,
pure evaluation services, bounded adapters and tests only.

It does not authorize operational activation, service restart,
rollback, public opening or Production.

## Architecture freeze conditions

ACTIVATION-01B architecture may freeze only when:

- This architecture is reviewed
- The read-only runbook is reviewed
- Existing canonical contracts are reused
- New schema names are fixed
- Module ownership is fixed
- Host command allowlist is fixed
- HTTP boundary is fixed
- CLI status and exit-code semantics are fixed
- No-mutation test strategy is fixed
- Production remains `NOT_AUTHORIZED`
