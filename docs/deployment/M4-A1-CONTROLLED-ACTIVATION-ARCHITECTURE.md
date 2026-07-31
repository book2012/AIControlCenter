# M4-A1 Controlled Activation Architecture

M4-A1 begins M4 with architecture-only contracts and closes with
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`. This decision is not an
activation request, authorization, permit, claim, or operational authorization.
M3 is closed at commit `89d10da82545e6cfd173085719076bb71e14c120`.

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

The 427 existing deprecation warnings remain a separate backlog track.
