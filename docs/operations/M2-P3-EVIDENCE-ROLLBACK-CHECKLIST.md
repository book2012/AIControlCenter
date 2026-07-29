# M2-P3 Evidence and Rollback Checklist

- [x] Validate exact permit, readiness, authorization and activation bindings.
- [x] Validate exact activation step and executor-result ordering.
- [x] Reject altered, duplicate, missing, unsafe and nonzero-safety evidence.
- [x] Derive rollback artifacts and typed steps only from valid evidence.
- [x] Require distinct rollback operator and allowed-role approver.
- [x] Reserve rollback before the first adapter operation and deny replay.
- [x] Confine the test adapter to a pytest temporary root.
- [x] Restore the pre-activation digest and remove activation artifacts.
- [x] Confirm no persistent-host or Production activation/rollback claim.

Any unchecked item is no-go. Production activation remains `NOT_AUTHORIZED`.
