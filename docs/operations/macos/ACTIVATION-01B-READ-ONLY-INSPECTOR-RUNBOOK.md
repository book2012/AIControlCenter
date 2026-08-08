# ACTIVATION-01B Read-Only Activation Inspector Runbook

<!-- AICONTROLCENTER:ACTIVATION_01B_OPERATIONAL_VALIDATION:START -->
## ACTIVATION-01B Read-Only Operational Validation

Status: `COMPLETE`

Classification: `PASS / FAIL-CLOSED`

The bounded read-only inspector completed the full Mac control-plane
observation path.

Inspector exit code: `2`

Overall status: `BLOCKED`

Inspection ID: `activation-inspection-7f2591c5066142dfaa383a31ae943f0d`

Report digest: `sha256:5afa71f7bd1edb1111203f0227a1cb3314a306cc1355ec465d33f5d10800e9e4`

Inspector commit: `698f60444894cb4f22c9cbc647abc2ee2a530e59`

Blocking reasons:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","HTTP_GET_HEALTH","HTTP_GET_RUNTIME_HEALTH","HTTP_POST_HEALTH_DENIED","LAUNCHD_RUNNING","LISTENER_COUNT_MATCH","LISTENER_PID_MATCH","PROCESS_SERVING_TARGET_MATCH"]`

Sanitized errors:

`[]`

Operational safety:

- Runtime mutations: `0`
- Service restarts: `0`
- Rollback executions: `0`
- launchd changes: `0`
- Caddy changes: `0`
- Public openings: `0`
- Production writes: `0`
- Ubuntu changes: `0`
- Production authorization: `NO`

`READY_FOR_AUTHORIZATION_REVIEW` is evidence readiness only.

A `BLOCKED` result is a successful fail-closed operational
validation. It does not authorize remediation or Production.

Notion synchronization remains pending as the final
project-management gate.
<!-- AICONTROLCENTER:ACTIVATION_01B_OPERATIONAL_VALIDATION:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_HTTP_CONTRACT_FIX:START -->
## ACTIVATION-01B HTTP Evidence Contract Correction

Status: `COMPLETE`

Operational validation exposed a direct-localhost
`HTTP_PROBE_FAILED` condition.

The registered HTTP evidence contract uses:

- `actual_status`
- `result`
- `body_length`
- `sanitized_error`
- `attempt_count`
- `redirect_followed`

Transport or connection failures are now represented as probe
evidence:

- `actual_status = null`
- `result = ERROR`
- `body_length = 0`
- bounded `sanitized_error`
- `attempt_count = 1`
- `redirect_followed = false`

The corresponding blocking inspection check fails.

A transport failure therefore resolves to `BLOCKED` rather than
being promoted to an inspector execution `ERROR`.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_HTTP_CONTRACT_FIX:END -->

<!-- AICONTROLCENTER:ACTIVATION_01B_LAUNCHD_SCOPE_FIX:START -->
## ACTIVATION-01B Launchd Parser Scope Correction

Status: `COMPLETE`

Operational validation discovered that `launchctl print` contains
nested resource and jetsam records whose field names overlap with the
top-level service record.

Observed example:

- service scope: `state = spawn scheduled`
- resource scope: `state = active`
- jetsam scope: `state = active`

The previous parser flattened all scopes and therefore emitted
`LAUNCHD_CONFLICTING_FIELD`.

The corrected parser is brace-depth aware and consumes identity,
state, pid, username and program arguments only from the service
record scope.

Nested launchd metadata is ignored rather than selected
heuristically.

Conflicting values within the service scope still fail closed.

The change affects observation logic only.

Runtime mutations: `0`
Service restarts: `0`
Rollback executions: `0`
launchd changes: `0`
Caddy changes: `0`
Public openings: `0`
Ubuntu changes: `0`
Production authorization: `NO`
<!-- AICONTROLCENTER:ACTIVATION_01B_LAUNCHD_SCOPE_FIX:END -->

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

Implemented invocation:

    python -m core.deployment.activation_inspector.runner --repository /Users/kyouhan/AIControlCenter --runtime-root "/Users/kyouhan/Library/Application Support/AIControlCenter/runtime" --json

The command performs bounded read-only inspection only.

It does not modify Runtime state, restart services, alter launchd or
Caddy, touch Ubuntu, open public access, or authorize Production.
<!-- AICONTROLCENTER:ACTIVATION_01B_C4:END -->

## Status

Gate:

`ACTIVATION-01B — Architecture Frozen`

This runbook describes future read-only inspection behavior.

No inspector implementation or operational inspection is authorized by this
document.

Production remains `NOT_AUTHORIZED`.

## Safety boundary

The future inspector may read bounded Mac Control Plane state only.

It must not:

- Change `runtime/current`
- Create or replace Runtime links
- Patch a finalized Runtime
- Install dependencies
- Start or restart a service
- Execute rollback
- Modify launchd
- Modify Caddy
- Open public access
- Contact Ubuntu
- Read secrets
- Grant authorization

## Canonical target

The future inspection target is bound to:

- Repository:
  `/Users/kyouhan/AIControlCenter`
- Runtime root:
  `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime`
- Candidate Runtime:
  `acd80ab9f6ae`
- Expected active Runtime:
  `b9ad351a7241`
- Canonical serving target:
  `core.api.shadow:app`
- LaunchDaemon:
  `system/com.aicontrolcenter.api.shadow`
- Application user:
  `kyouhan`
- Listener:
  `127.0.0.1:18100`
- Mutating probe:
  `POST /health` expects HTTP `405`

These values are inspection policy inputs. They are not authorization.

## Planned read-only sequence

1. Load and validate the versioned activation policy.
2. Load and validate the versioned localhost route manifest.
3. Capture bounded Git evidence.
4. Read `runtime/current` without following mutation paths.
5. Read Runtime metadata and the source marker.
6. Inspect the Runtime Python executable and version.
7. Record effective repository `PYTHONPATH` coupling.
8. Inspect the exact LaunchDaemon with `launchctl print`.
9. Inspect the exact listener with machine-readable process evidence.
10. Match listener PID to the LaunchDaemon application PID.
11. Execute direct-localhost HTTP probes in manifest order.
12. Build deterministic checks and blocking reasons.
13. Validate the report against the registered JSON Schema.
14. Compute the canonical report digest.
15. Emit canonical JSON.
16. Exit without changing host state.

## Allowed external commands

The implementation may allow only exact read-only commands.

Initial allowlist:

```text
git
launchctl print system/com.aicontrolcenter.api.shadow
/usr/sbin/lsof field-mode listener inspection
exact Runtime Python `-I -S --version`
```

Git command arguments must be supplied by the existing bounded
`git_readonly_evidence` capability.

No command may be constructed from unvalidated free-form policy content.

## Prohibited command families

The implementation must reject:

```text
launchctl kickstart
launchctl bootstrap
launchctl bootout
launchctl enable
launchctl disable
sudo
kill
killall
pkill
mv
ln
rm
cp
install
pip install
curl to a public host
ssh
scp
rsync
docker
docker compose
```

This list is not an alternative-command search mechanism.

Unknown commands fail closed.


<!-- AICONTROLCENTER:ACTIVATION_01B_PROBE_HARDENING -->
## Runtime Python probe safety

The only allowed Runtime Python process invocation is:

    <exact-runtime-python> -I -S --version

The implementation must use:

- The absolute Runtime Python path
- `shell=False`
- A bounded timeout
- A sanitized environment
- `PYTHONNOUSERSITE=1`
- `PYTHONDONTWRITEBYTECODE=1`
- A deterministic locale

The implementation must not execute:

- Application imports
- Package imports
- Python source files
- Python expressions
- `pip`
- `pip freeze`
- Dependency installation
- Arbitrary environment-provided startup code

Dependency identity must be read from finalized evidence rather than discovered
through installed package execution.

## Method-denial probe safety

The future inspector may verify only this denied method:

    POST http://127.0.0.1:18100/health

Required request constraints:

- Zero-length body
- No cookies
- No credentials
- No authorization header
- No caller-provided headers
- One attempt only
- No redirect following
- No automatic retry
- Expected result: HTTP `405`

The inspector must fail closed on every other result.

This probe confirms denial behavior only.

It does not authorize HTTP mutation or establish a general POST capability.

## HTTP behavior

HTTP inspection must:

- Connect only to `127.0.0.1:18100`
- Use the exact manifest method and path
- Use a bounded timeout
- Disable automatic retries
- Reject redirects
- Send no cookies
- Send no authorization header
- Record status and sanitized error type
- Close every connection

The inspector must not infer success from connection availability alone.

## Output behavior

Canonical JSON is the source of truth.

Human-readable output, when supported, must be derived from the JSON report.

The report must never contain:

- Passwords
- Tokens
- API keys
- Cookies
- Authorization headers
- Private keys
- Environment-variable values
- Raw secret-bearing command output

## Stop conditions

Inspection must stop or return a blocking result when:

- Policy validation fails
- Route-manifest validation fails
- Git evidence is unavailable
- Repository HEAD is unexpected
- Working tree is not clean
- Runtime pointer is missing or malformed
- Active Runtime differs from policy
- Candidate Runtime is unavailable
- Metadata or source marker is invalid
- Python identity differs
- launchd identity is unavailable or mismatched
- Application process runs as an unexpected user
- Listener is not loopback-only
- Listener PID does not match the service PID
- More than one listener is observed
- Any required GET route does not return HTTP `200`
- `POST /health` does not return HTTP `405`
- Evidence Schema validation fails
- Canonical digest construction fails
- Any mutation is detected

## Result interpretation

`READY_FOR_AUTHORIZATION_REVIEW` means evidence matched the inspection
policy.

It does not authorize:

- Runtime activation
- Service restart
- Rollback
- Public opening
- Production

`BLOCKED` requires human review and a new inspection after the blocking
condition is resolved.

The inspector must not repair, retry through another mechanism or select a
substitute Runtime.

## Operational evidence

Future real-host inspection evidence must record:

- Exact policy digest
- Exact route-manifest digest
- Exact Git evidence digest
- Runtime pointer identity
- Runtime metadata identity
- Source marker identity
- Python identity
- launchd identity
- Process identity
- Listener identity
- Per-route HTTP results
- Overall status
- Blocking reasons
- Report digest

Evidence capture does not grant authorization.

## Architecture freeze record

- Status: `FROZEN`
- Freeze date: `2026-08-05`
- Predecessor commit:
  `43975f6e26986fd91c9a715786e7c68deb63f612`
- Inspector implementation: `NOT_STARTED`
- Real-host inspection: `NOT_EXECUTED`
- Runtime mutation count: `0`
- Service restart count: `0`
- Production authorization: `NOT_AUTHORIZED`

Implementation may proceed only within the frozen read-only
boundaries defined by this runbook and the architecture document.

## Current state

At creation of this runbook:

- Runtime mutation count: `0`
- Service restart count: `0`
- Rollback execution count: `0`
- launchd modification count: `0`
- Caddy modification count: `0`
- Ubuntu modification count: `0`
- Public opening count: `0`
- Production authorization:
  `NOT_AUTHORIZED`
