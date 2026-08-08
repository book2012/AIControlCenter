# ACTIVATION-01C Controlled Activation Architecture

<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:START -->
## ACTIVATION-01C Controlled Pointer Activation

Status: `COMPLETE`

Authorized transition:

`b9ad351a7241 -> acd80ab9f6ae`

Runtime pointer activation:

`PASS`

Activation report SHA-256:

`d59a3aa81accca4e6f330c85774924221e33e247376a069a1d922f5716dec24a`

Natural launchd KeepAlive recovery:

`PASS`

Explicit service restart commands:

`0`

Launchd state:

`running`

Listener:

`127.0.0.1:18100`

Listener/PID correlation:

`PASS`

Approved wrapper SHA-256:

`a58d926f8845f6b0aa7863250b02c0c461ea843bfa03a83313eaaa547ca98212`

Wrapper serving target:

`core.api.shadow:app`

HTTP validation:

- `GET /health -> 200`
- `GET /runtime/health -> 200`
- `POST /health -> 405`

Post-activation ACTIVATION-01B inspection ID:

`activation-inspection-bc8f2b34d45242c4b835d4ba852667a3`

Post-activation report digest:

`sha256:f419242b927804a6c97ad947ad4eb2deb9b2a07545724d750fd85ab3a80def22`

01B terminal status:

`BLOCKED`

Remaining transition-phase blockers:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","PROCESS_SERVING_TARGET_MATCH","RUNTIME_CURRENT_MATCH"]`

Operational Runtime, launchd, listener and HTTP checks passed.

The residual blockers are contract-phase mismatches:

- pre-activation Runtime expectation
- Control Plane Git identity versus Candidate source identity
- launchd wrapper indirection versus direct serving-target inference

01C independently verifies the exact approved wrapper SHA and its
static `uvicorn core.api.shadow:app` exec chain.

Rollback executions:

`0`

Explicit launchd mutation commands:

`0`

Caddy changes:

`0`

Public openings:

`0`

Ubuntu changes:

`0`

Production authorization:

`NO`

ACTIVATION-01C does not constitute PI-009 Production authorization.
<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:END -->

Status: `AUTHORIZATION_CONTRACT_FROZEN`

Production authorization: `NO`

## Purpose

ACTIVATION-01C introduces one narrowly bounded mutation capability
after ACTIVATION-01B completed read-only operational validation.

The first authorized mutation is an atomic Runtime pointer activation.

It does not grant general shell authority, service-management
authority, rollback authority, public-opening authority, Ubuntu
authority or Production authorization.

## Observed Pre-Activation State

Active Runtime: `b9ad351a7241`

Candidate Runtime: `acd80ab9f6ae`

Candidate source commit: `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

Candidate startup dependency probe: `PASS`

Candidate `jsonschema` import: `PASS`

Candidate `uvicorn` import: `PASS`

Candidate `core.api.shadow:app` import: `PASS`

Current shadow daemon state before authorization:

- registered LaunchDaemon
- KeepAlive enabled
- RunAtLoad enabled
- no listener on `127.0.0.1:18100`
- previous runtime repeatedly exits
- direct observed failure: missing `jsonschema` in `b9ad351a7241`

## Mutation Boundary

Only the canonical Runtime bootstrap activation operation may mutate
the Runtime pointer.

Exact authorized command template:

    bash ops/macos/runtime/bootstrap-production-runtime.sh --mode activate --release "/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/acd80ab9f6ae" --expected-source-commit "acd80ab9f6aeb848900e1a19e3fa3afd69face8a"

Canonical bootstrap SHA-256:

`41c7a485fada331439b9e5ef47ebe6b78d0674bb7b3ba15264d0604a156a480a`

The activation script validates the release path, source identity,
Runtime executable and activation target before replacing
`runtime/current`.

The pointer replacement is implemented through a temporary symlink
followed by an atomic move.

## Explicitly Not Authorized

The following operations remain prohibited:

- `launchctl kickstart`
- `launchctl bootstrap`
- `launchctl bootout`
- manual service restart
- launchd plist modification
- wrapper modification
- Candidate Runtime modification
- dependency installation into an immutable Runtime
- Caddy modification
- public opening
- Ubuntu modification
- automatic rollback
- Production authorization

## Existing KeepAlive Behavior

The registered LaunchDaemon already owns KeepAlive and RunAtLoad
behavior.

A natural retry caused by existing launchd policy after the Runtime
pointer changes is observed system behavior and is not a separately
issued operator restart command.

No explicit service-control operation is authorized by the first
01C permit.

## Post-Activation Validation

After pointer activation, the previously validated ACTIVATION-01B
read-only inspector must run without implementation changes.

Validation must inspect:

- Runtime pointer identity
- Runtime source identity
- launchd state
- process identity
- listener identity
- PID correlation
- exact localhost HTTP probes
- Git evidence
- Production safety fields

No inspector result grants Production authorization.

## Rollback Boundary

The pre-activation Runtime `b9ad351a7241` is rollback evidence only.

Rollback requires a new explicit human authorization and a separately
bounded activation command targeting the previous immutable Runtime.

No automatic rollback is permitted.

## Production Boundary

ACTIVATION-01C is not the PI-009 Production activation approval.

Production remains `NOT_AUTHORIZED`.
