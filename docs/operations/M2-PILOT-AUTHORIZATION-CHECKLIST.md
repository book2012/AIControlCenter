# M2 Pilot Authorization Checklist

- [ ] DPL-03C execution authorization validates and is unexpired.
- [ ] DPL-04D readiness decision is exactly
      `READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX`.
- [ ] Readiness report ID and canonical digest match.
- [ ] Package, plan, target and environment bindings match exactly.
- [ ] Target owner is `mac-control-plane`.
- [ ] Environment is `development`, `test` or `staging`.
- [ ] Scope contains only the three allowed typed sandbox operations.
- [ ] Sandbox-root identity digest and safe nonce reference are present.
- [ ] Requester, operator and approver identities are non-empty.
- [ ] Requester and operator are each different from the approver.
- [ ] Approver role is explicitly accepted.
- [ ] Issue and expiry timestamps are explicit, ordered and within one hour.
- [ ] `max_uses` is exactly one.
- [ ] Every safety counter is zero.
- [ ] `production_authorized` is false.
- [ ] Pilot activation is not requested and has not started.
- [ ] Persistent SQLite audit is not claimed operational.
- [ ] No secret, raw environment, shell, command, argv or script field exists.

Any unchecked item is no-go. Authorization creates policy evidence only; it
does not consume a permit or execute the pilot. Persistent SQLite audit remains
not implemented and Production activation remains `NOT_AUTHORIZED`.
