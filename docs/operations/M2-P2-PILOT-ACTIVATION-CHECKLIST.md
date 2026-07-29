# M2-P2 Pilot Activation Checklist

- [ ] Valid M2-P1 permit ID and canonical digest match.
- [ ] Permit is unexpired, `max_uses=1`, and activation flag is false.
- [ ] Accepted readiness report ID, digest and decision remain unchanged.
- [ ] Package, plan, authorization, target and environment bindings match.
- [ ] Target owner is `mac-control-plane`; target is not Ubuntu.
- [ ] Environment is `development`, `test` or `staging`.
- [ ] Requested scope is exactly the three approved typed operations.
- [ ] Sandbox-root identity digest matches.
- [ ] Requester, operator and approver identities match the permit.
- [ ] Production authorization and persistent-audit claims are false.
- [ ] Every input safety counter is zero.
- [ ] Typed executor, capability and permit-use registry are injected.
- [ ] Permit is reserved before the first adapter invocation.
- [ ] Operation order is verify, prepare, collect evidence.
- [ ] Each result matches its request and capability.
- [ ] Each result reports false production authorization and zero safety
      counters.
- [ ] Any failed attempt leaves the permit consumed and replay denied.
- [ ] Artifacts are confined to a pytest-owned temporary directory.
- [ ] No repository/system write, network, subprocess, runtime command,
      service restart, API write route or Ubuntu access occurs.

Any unchecked item is no-go. The in-memory permit registry is process-local and
is not sufficient for broader mutable deployment. Persistent host activation
is not started, persistent SQLite audit is not implemented, and Production
activation remains `NOT_AUTHORIZED`.
