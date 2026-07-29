# M2-P1 Controlled Non-Production Sandbox Pilot Authorization

Status: **CLOSED**

## Decision

`core.deployment.pilot_authorization` provides pure immutable policy contracts
and a deterministic default-deny authorization service. It creates no runtime
capability beyond a policy permit and does not execute, activate, consume,
persist or expose an API.

An authorized permit binds the valid DPL-03C execution authorization and
accepted DPL-04D readiness report to their identifiers and digests, the package
and plan digests, exact Mac target, development/test/staging environment,
typed sandbox operation scope, sandbox-root identity digest, requester,
operator, approver and accepted approver role, safe nonce reference, explicit
issue and expiry timestamps, and `max_uses=1`.

## Allowed boundary

- Target owner: `mac-control-plane`
- Environments: `development`, `test`, `staging`
- Operations: `VERIFY_SANDBOX_TARGET`, `PREPARE_SANDBOX`,
  `COLLECT_EXECUTION_EVIDENCE`
- Readiness decision:
  `READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX`
- Production authorization: `false`
- Pilot activation started: `false`

Production aliases, Ubuntu/external ownership, arbitrary operations, commands,
shell, argv, scripts, secret-bearing fields, identity contradictions, invalid
or expired evidence, nonzero safety counters, activation requests and claims
of operational persistent SQLite audit are denied or blocked.

## Non-effects

M2-P1 adds authorization policy only. It performs zero executor, sandbox
adapter, filesystem artifact, persistent audit, nonce, database, network,
Ubuntu, service, API-write, pilot-activation and production-activation
operations. The persistent SQLite audit adapter is `NOT IMPLEMENTED`.
Production activation remains `NOT_AUTHORIZED`.

## Status

- DPL-04: `CLOSED`
- M2 readiness: `ACCEPTED`
- M2-P1: `CLOSED`
- Pilot authorization policy: `AVAILABLE`
- Pilot activation: `NOT STARTED`
- Next: M2-P2 Controlled Sandbox Pilot Activation and Evidence
