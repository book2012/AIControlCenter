# M4-A1 Controlled Activation Architecture

M4-A1 begins M4 with architecture-only contracts and closes with
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`. This decision is not an
activation request, authorization, permit, claim, or operational authorization.
M3 is closed at commit `89d10da82545e6cfd173085719076bb71e14c120`.
The M4-A1 implementation commit is
`b719aa445af864c907ac5d384c2c8347d2d6688a`.

## M4-A1R1 retained snapshot isolation

M4-A1R1 closes a deployment-test fixture boundary without changing M4-A1
architecture or production validation semantics. An injected retained source
snapshot is immutable and is used only to construct disposable working copies.
Every SQLite inspection and recovery test receives a working copy below the
injected recovery workspace. The M3-A4B3 validator also copies each database
and its existing WAL and SHM files into a disposable inspection directory
before opening SQLite.

Fixture regression checks preserve retained-source bytes, modes, sizes, mtimes,
and SHA-256 digests. SQLite WAL/SHM access side effects are confined to working
copies. The injected M3-A4B3 bindings, cryptographic identifiers, digests,
claim rules, evidence validation, and fail-closed production semantics are
unchanged. The pristine retained copies are not exposed to Codex, and actual
operational state remained unchanged.

Validation requires no `.env` file. M4-A1 and M4-A1R1 are architecture-only:
no authorization, permit, claim, activation, writer, monitoring runtime,
dispatch, Ubuntu change, runtime command, API write route, or production
authorization was created. The decision remains
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`; production remains
`NOT_AUTHORIZED`.

## Control-plane boundary

AIControlCenter owns the capability registry, governance, authorization
boundary, state transition policy, deterministic planning, and validation. The
Mac remains the always-on brain and single control plane. Ubuntu remains an
optional stateless infrastructure worker and is ineligible for governance,
authorization, business logic, audit, replay, activation, or state ownership.
Production remains `NOT_AUTHORIZED`.

No writer, monitoring runtime, dispatch adapter, API write route, subprocess,
network client, arbitrary command path, or operational activation was added.

## Capability registry

The closed registry is ordered `AUDIT_WRITER`, `REPLAY_WRITER`,
`MONITORING_RUNTIME`, `ALERT_DISPATCH`, `EXTERNAL_NOTIFICATION`. Every
capability starts `INACTIVE` and unauthorized, requires an independent
approval, a capability-scoped single-use permit, exactly one atomic claim,
rollback evidence, and fail-closed validation. Every capability is
production-ineligible and Ubuntu-ineligible.

`AUDIT_WRITER` and `REPLAY_WRITER` have no runtime capability dependency.
`MONITORING_RUNTIME` may require read-only audit and replay health, but never
writer activation. `ALERT_DISPATCH` depends on separately authorized
`MONITORING_RUNTIME`; `EXTERNAL_NOTIFICATION` depends on separately authorized
`ALERT_DISPATCH`. Dependency satisfaction never grants authorization and never
adds a capability to a request.

## State machine

The exact success chain is:

`INACTIVE → REQUESTED → INDEPENDENTLY_APPROVED → AUTHORIZED → PERMITTED →
CLAIMED → CONTROLLED_ACTIVE → VALIDATED → DEACTIVATED`.

`BLOCKED` and `FAILED_CLOSED` are terminal failure outcomes. Transitions are
immutable, deterministic, bound to the exact feature branch and M3 closeout
commit, and require typed evidence. Skips, backward transitions, permit reuse,
duplicate claims, activation before a claim, environment-only activation,
production transitions, and Ubuntu delegation fail closed.

## Deterministic planner

The planner accepts only a controlled non-production request bound to the exact
branch, commit, M3 readiness decision, requester, operator, and independent
approver. It ignores caller ordering by rejecting it, applies registry order,
and emits capability-scoped gates, authorization-contract requirements, permit
and claim boundaries, evidence, rollback, dependencies, prohibited
transitions, a canonical JSON result, and a deterministic SHA-256 digest.

Planning has no operational side effects and creates zero authorizations,
permits, claims, activations, writers, monitoring runtimes, or dispatches.
Capability authorization contracts remain future work in M4-A2.

## Default deny

Validation rejects invalid Git or M3 bindings, production or Linux live-control
scope, root operation, requester/approver collision, unknown or duplicate
capabilities, caller ordering, missing evidence or rollback, expired
authorization, reusable permits, duplicate claims, implicit escalation,
external governance or business-logic authority, Ubuntu ownership,
environment-only activation, arbitrary commands, and runtime subprocesses.

M4-A1R1 validation passed 958 deployment tests and the 1,942-test full
regression suite, with 5 repository-configured deselections, 427 existing
warnings, and zero failures. The warnings remain a separate backlog track.
