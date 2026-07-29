# DPL-03D Simulation-Only Apply Composition

DPL-03D closes DPL-03 with a pure, non-production simulation boundary. It
does not provide real deployment capability. `SimulationApplyService` accepts
an exact DPL-03C `ExecutionAuthorization`, a validated DPL-03B plan, explicit
binding values, and caller-supplied timestamps. No API route is added.

## Ownership and sequence

AIControlCenter on the Mac mini remains the only Control Plane.
`FakeDeploymentExecutor` is owned by the simulation package and accepts only
immutable `SimulationIntent` values. An intent cannot carry shell, command,
argv, script, secret, or path-based runtime instructions.

The service validates schema and security constraints, validates the plan and
its digest and graph, checks exact package/plan/target/environment/scope
bindings, confirms READY_FOR_APPROVAL with no CRITICAL risk, checks explicit
non-production environment and expiry, and requires a one-use authorization.
Only then does it atomically consume the authorization ID and nonce through a
dependency-injected `InMemoryReplayGuard`. A missing replay guard or fake
executor denies the request.

Nonce consumption is fail-closed: once consumed, it remains consumed even if
the fake executor fails. This prevents authorization reuse after an uncertain
fake-execution result.

## Receipt and safety

The fake executor deterministically describes simulated results and performs
no filesystem mutation, subprocess execution, network access, environment
mutation, Ubuntu access, or Caddy, Docker, Compose, Colima, or launchctl
command. `SIMULATED` means only that this fake produced its deterministic
description; it never means infrastructure changed.

Receipt identity and digest derive only from canonical semantic inputs,
including explicit start and completion timestamps. The receipt contains a
nonce digest, never the raw nonce. It reports simulation mode, fake executor,
no production authorization, zero production writes, Ubuntu changes, network
accesses and runtime commands, and one fake invocation.

The replay guard is process-local and non-persistent. There is no global
singleton, nonce database, audit database, production authorization, or
production activation. Restarting a process loses replay memory, so this
composition is intentionally unsuitable for real apply.

## Closure

DPL-03D and DPL-03 are complete when schema, determinism, authorization
binding and consumption, replay behavior, security denials, dependency
boundaries, DPL-03B and DPL-03C compatibility, namespace separation,
deployment tests, and full regression all pass.

This closes the planning/authorization/simulation milestone only. M2 is not
complete. DPL-04 is the next separately gated milestone and must not infer
production activation authority from any DPL-03 artifact.
