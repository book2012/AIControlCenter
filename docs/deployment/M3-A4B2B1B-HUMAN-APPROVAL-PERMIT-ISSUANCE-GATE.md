# M3-A4B2B1B Human Approval and Permit Issuance Gate

Status: CLOSED after validation.

The `operational_permit_approval` package is the deterministic boundary between
the M3-A4B2B1A review package and the M3-A4B1 public authorization service. It
validates the exact review-package ID/digest, branch and commit, structured
requester/operator/approver identities, identity independence, dual
restriction acknowledgements, the 427-warning binding, the effective execution
window, zero safety counters, target absence, and non-production scope.

Only `HUMAN_APPROVAL_AND_PERMIT_ISSUANCE_REVIEW` is supported. The coordinator
rejects adapters, claims, execution, persistence, notification and production
authorization. When every gate passes it may delegate to M3-A4B1 only for a
clearly synthetic test identity set and returns the permit in memory. It never
creates a duplicate permit model.

The current recommended review remains non-authorizing:

- requester and Mac operator: `mac-account:kyouhan`
- independent approver: `UNASSIGNED`
- independent approval: `NOT PROVIDED`
- independent restriction acknowledgement: `NOT PROVIDED`
- decision: `DENIED`
- reasons: `MISSING_INDEPENDENT_APPROVER`,
  `MISSING_INDEPENDENT_ACKNOWLEDGEMENT`
- effective execution window: none
- operational permit: `NOT ISSUED`
- permit claim: `NOT CLAIMED`
- operational bootstrap: `NOT AUTHORIZED`, `NOT EXECUTED`
- production activation: `NOT_AUTHORIZED`

Synthetic dual-identity approval and synthetic in-memory permit issuance are
validated capability tests only. No live operational permit artifact exists.
