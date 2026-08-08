# ACTIVATION-01C Controlled Activation Architecture

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
