# M2 Non-Production Sandbox Runbook

## Scope

This runbook governs a separately authorized Mac-only non-production sandbox
pilot. M2-P2 permits only a test-owned activation below a pytest temporary
root; it does not authorize persistent host or Production activation.

## Procedure

1. Confirm DPL-04A through DPL-04D are closed and use the canonical evidence
   schema and explicit timestamp.
2. Collect read-only evidence outside the gate without secrets, commands,
   raw environments or production authorization.
3. Evaluate all thirteen categories and retain canonical report JSON and
   digest.
4. Proceed to a pilot authorization request only when the decision is
   `READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX`.
5. Stop on `NOT_READY` or `BLOCKED`; correct or recollect evidence and create a
   new report.
6. Use the M2-P1 policy only to validate exact bindings, separation of duties,
   typed operation scope, one-use lifetime and zero safety counters.
7. Inject the typed executor, capability and permit-use registry; never
   construct an adapter inside the activation service.
8. Reserve the permit before invocation, then execute only verify target,
   prepare sandbox and collect evidence in that order.
9. Stop on any invalid, denied, unavailable, incomplete, malformed, mismatched
   or nonzero-safety result. A failed attempt remains consumed.
10. Confine canonical manifest and evidence artifacts to the pytest-owned
    temporary sandbox and retain the immutable activation receipt.

The operator must preserve a non-repository sandbox root, Mac Control Plane
ownership, zero Ubuntu/runtime/network/production activity, and zero real
executor invocations. Persistent SQLite audit must be implemented and
separately authorized before any broader mutable deployment.

M2-P1 and M2-P2 are closed. Exactly one controlled pilot was exercised only in
a pytest-owned temporary sandbox. Persistent host sandbox activation has not
started. Production activation remains `NOT_AUTHORIZED`.
