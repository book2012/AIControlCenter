# M3-A4B2B1A Operational Permit Issuance Control

## Status

M3-A4A, M3-A4B1, M3-A4B2A, M3-A4B2B0 and M3-A4B2B1A are CLOSED after
validation. The permit issuance review package is AVAILABLE. It is evidence
for a future human decision, never an issuance decision.

Human operator identity is NOT PROVIDED. Independent approver identity is NOT
PROVIDED. Restriction acknowledgements are NOT PROVIDED. The operational
permit is NOT ISSUED or CLAIMED; bootstrap is NOT AUTHORIZED or EXECUTED;
operational targets are NOT CREATED; production activation is NOT_AUTHORIZED.

## Boundary

`core.deployment.operational_permit_issuance` is pure and deterministic. It
binds the public readiness, authorization-capability, test-only executor and
read-only host-preflight evidence by canonical digest. It accepts no adapter,
performs no I/O, calls no clock, creates no identity or acknowledgement, and
does not duplicate the M3-A4B1 permit contract.

Only `OPERATIONAL_PERMIT_ISSUANCE_REVIEW` is supported. Privileged, operational
and production stages fail closed. Exact branch/commit, source reports,
target/schema/plan identity digests, test and Git parity, target absence,
Darwin ownership, capacity, permissions and all-zero counters are bound.

The 427 existing deprecation warnings remain a nonblocking restriction with
acknowledgement required and acknowledgement absent. Human inputs are missing
review prerequisites, not implementation defects. Identical semantic inputs
produce identical ordered content, IDs, canonical JSON and digests.

Next task: M3-A4B2B1B Operator Approval and Operational Permit Issuance.
