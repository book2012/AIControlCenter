# M4 Controlled Activation Checklist

This checklist describes future gates only. M4-A1 does not authorize or perform
activation.

## Capability authorization boundary

- Bind one explicitly requested capability to the exact approved feature branch
  and commit.
- Keep its initial state `INACTIVE` and authorization false.
- Record distinct requester and independent approver identities; prohibit root.
- Require a capability-scoped bounded authorization contract.
- Issue no permit until a future separately authorized task permits issuance.
- Require a single-use permit and exactly one atomic claim.
- Treat capability dependencies as prerequisites, never as authorization.
- Require immutable evidence at every transition and rollback evidence before
  controlled deactivation.
- Fail closed on any missing, invalid, reused, duplicate, expired, or mismatched
  representation.

## M3-to-M4 boundary

- M3 is closed with
  `READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION`.
- Bind future work to M3 closeout commit
  `89d10da82545e6cfd173085719076bb71e14c120`.
- M4-A1 yields only `READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS`.
- Do not interpret either readiness decision as operational authorization.

## Default-deny operations

- Keep Mac as the AIControlCenter brain and single control plane.
- Keep Ubuntu stateless and outside governance, authorization, state, audit,
  replay, business logic, and activation.
- Keep production `NOT_AUTHORIZED`.
- Keep API routes, n8n, WordPress, and WooCommerce outside activation authority.
- Prohibit environment-only activation, generic commands, subprocess execution,
  service restarts, runtime writers, monitoring runtime, and external dispatch.
- Independently authorize `MONITORING_RUNTIME`, `ALERT_DISPATCH`, and
  `EXTERNAL_NOTIFICATION`; never infer downstream capability permission.

The 427 deprecation warnings remain a separate backlog item.
