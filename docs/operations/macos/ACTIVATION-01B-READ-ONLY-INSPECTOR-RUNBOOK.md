# ACTIVATION-01B Read-Only Activation Inspector Runbook

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
