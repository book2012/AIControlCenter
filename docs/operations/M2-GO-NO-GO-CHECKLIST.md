# M2 Go/No-Go Checklist

- [ ] Canonical evidence is complete, immutable and secret-free.
- [ ] All thirteen mandatory checks pass.
- [ ] Regression evidence is at least 1247 passed with zero failures.
- [ ] Git branch, commit, push, clean tree and synchronization evidence pass.
- [ ] Every safety counter is zero.
- [ ] Decision is `READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX`.
- [ ] Sandbox-only, Mac-only and non-production restrictions are accepted.
- [ ] No real executor, Ubuntu execution, public write API or production
      authorization exists.
- [ ] M2-P1 operator authorization and separation-of-duty checks pass.
- [ ] The one-use permit binds exact target, environment, operation scope,
      sandbox-root identity and evidence digests.
- [ ] Pilot activation has not already occurred.

Any unchecked item is no-go. Warnings must remain visible. The missing
persistent SQLite audit adapter is an explicit restriction and blocks broader
mutable deployment, though it does not block this sandbox-only readiness
decision.

M2-P1 is closed and authorization policy is available. This checklist does not
start the pilot; activation remains an M2-P2 action. Production activation is
`NOT_AUTHORIZED`.
