# M3-A4 Controlled Bootstrap Plan

This immutable plan is planning-only and performs no bootstrap or activation.

1. Revalidate Git clean state and the approved commit.
2. Revalidate full regression and all safety counters.
3. Require explicit non-production operator approval.
4. Create Mac application-state parent directories.
5. Apply restrictive directory permissions.
6. Create the audit ledger with an authorized bootstrap adapter.
7. Apply append-only audit schema and controls.
8. Inspect the audit database read-only.
9. Create the permit/replay database with an authorized bootstrap adapter.
10. Apply replay schema, indexes and immutable triggers.
11. Inspect the replay database read-only.
12. Create a baseline audit backup.
13. Create a baseline replay backup.
14. Validate both restores into temporary validation targets.
15. Generate a `PRE_ACTIVATION` monitoring snapshot.
16. Verify logical alert routing without external dispatch.
17. Keep operational writers disabled.
18. Return evidence for a separate activation decision.

The future bootstrap must fail closed: partial audit and replay cleanup is
defined; pre-existing files may not be overwritten; backup-before-activation
and restore validation are required; writer and monitoring activation can be
withheld; external dispatch remains unavailable; failure cannot produce
`ACTIVE`; and operator escalation is documented.

The plan grants no Production authorization, external dispatch, Ubuntu
participation, API write route, service restart or writer activation. The plan
does not activate anything. Bootstrap authorization is `NOT GRANTED` and
Production activation is `NOT_AUTHORIZED`.
