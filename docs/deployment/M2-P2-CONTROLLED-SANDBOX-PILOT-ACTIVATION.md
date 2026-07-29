# M2-P2 Controlled Sandbox Pilot Activation

Status: **CLOSED**

## Decision

`core.deployment.pilot_activation` provides immutable activation contracts and
a fail-closed orchestration service. It accepts an already validated M2-P1
permit, accepted M2 readiness evidence, exact execution authorization, an
injected typed executor port and capability, and an injected permit-use
registry. Production code does not construct or import `MacSandboxAdapter`.

The service reserves the one-use permit before adapter invocation and issues
exactly `VERIFY_SANDBOX_TARGET`, `PREPARE_SANDBOX`, then
`COLLECT_EXECUTION_EVIDENCE`. Every result is rebound to its request and
capability and must report false production authorization and zero repository,
production, Ubuntu, network and runtime-command counters. Any denied, invalid,
unavailable, incomplete, malformed, mismatched or unsafe result stops
immediately. A failed attempt remains consumed and replay is denied.

## Pilot evidence

Automated validation exercised exactly one successful controlled pilot with an
explicitly injected `MacSandboxAdapter` below a pytest-owned temporary
directory. Only canonical manifest and evidence JSON were materialized there.
No host-level or persistent sandbox was activated. Repository and system
directories, the network, subprocesses, service commands and Ubuntu were not
used.

Receipts bind activation, permit, execution authorization, readiness, package,
plan, target, environment and sandbox-root identities to ordered steps,
executor result digests, sorted evidence digests, safety counters and a
canonical receipt digest. `ACTIVATED` means only that the test-owned sandbox
pilot completed.

## Replay limitation

`InMemoryPilotPermitUseRegistry` is process-local and allowed only for isolated
tests and single-process controlled pilot validation. It is not sufficient for
broader mutable deployment. No persistent registry, database, migration,
SQLite audit adapter or durable audit write is implemented.

## State

- DPL-04: `CLOSED`
- M2 readiness: `ACCEPTED`
- M2-P1: `CLOSED`
- M2-P2: `CLOSED`
- Controlled pytest pilot activations: `1`
- Persistent host sandbox activation: `NOT STARTED`
- Persistent SQLite audit adapter: `NOT IMPLEMENTED`
- Production activation: `NOT_AUTHORIZED`
- Next: M2-P3 Pilot Evidence and Rollback Validation
