# M4-A2 Capability Authorization Contracts

## Decision

M4-A2 is contract, canonical validation, and deterministic test-only planning
only. Its decision is `READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION`. That
decision creates no authorization, operational permit, claim, writer,
monitoring runtime, dispatch, external notification, or activation.

M4-A1 and M4-A1R1 are closed. M4-A2 binds requests to branch
`feature/deployment-package`, baseline
`cbeb20d41808ea615b08196b164d6b5578486ed8`, M3 readiness
`READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`, and M4-A1 decision
`READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`.

## Contracts and validation

Immutable typed scope, request, approval, restriction, decision, evidence,
validation, grant-plan, plan, and architecture-decision contracts use canonical
JSON and SHA-256 digests. Datetimes must be timezone-aware and normalize to
UTC. Validation receives an injected clock and permits at most a one-hour,
single-use window. Cryptographic identity verification is deliberately absent
and recorded false.

Requester, Mac operator, and independent approver identities must be present.
The approver differs from requester and operator. Root, Ubuntu, API, n8n,
WordPress, WooCommerce, and external components cannot own authorization
governance. Production and Ubuntu participation are denied.

## Independent capabilities

Each request and approval binds exactly one M4-A1 capability. `AUDIT_WRITER`
and `REPLAY_WRITER` require single-use, atomic-claim, rollback-evidence, and
denial acknowledgements. `MONITORING_RUNTIME` requires exact read-only health
evidence and implies no writer or alert dispatch. `ALERT_DISPATCH` requires a
separate monitoring authorization reference; `EXTERNAL_NOTIFICATION` requires
a separate alert-dispatch reference. Dependencies never authorize, and
external endpoint details and secrets are outside M4-A2.

All restriction acknowledgements must be exact and complete. Digest, branch,
commit, capability, identity, readiness, time, scope, or dependency tampering
fails closed.

## Safety boundary

The planner emits a grant-shaped test plan whose authorization, permit, claim,
and runtime-activation fields are false and operational counters are zero. It
exposes no issuance, claim, activation, command, API write, network, Ubuntu, or
production adapter. `.env` is not required and was not read. Production
remains `NOT_AUTHORIZED`. The existing 427 deprecation warnings are separate
backlog.

## Verification

The M4-A2 targeted suite passed 59 tests, all deployment tests passed 1,016
tests with 9 warnings, and the full suite passed 2,000 tests with 5 configured
deselections and the existing 427 warnings. No test was weakened and no
operational state was accessed.

## M4-A3 follow-on closure

M4-A3 is closed as deterministic in-memory test-only simulation. M4-A2 plans
remain non-operational inputs. M4-A3 artifacts cannot enter live boundaries or
become operational through field renaming. No real authorization or activation
occurred. Decision: `READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION`.
