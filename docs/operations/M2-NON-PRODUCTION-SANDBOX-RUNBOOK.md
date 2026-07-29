# M2 Non-Production Sandbox Runbook

## Scope

This runbook prepares a separately authorized Mac-only non-production sandbox
pilot. It does not authorize or perform activation.

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
7. Treat an authorized permit as policy evidence only. M2-P2 requires separate
   authorization before any activation or evidence collection.

The operator must preserve a non-repository sandbox root, Mac Control Plane
ownership, zero Ubuntu/runtime/network/production activity, and zero real
executor invocations. Persistent SQLite audit must be implemented and
separately authorized before any broader mutable deployment.

M2-P1 is closed and pilot authorization policy is available. Pilot activation
has not started. Production activation remains `NOT_AUTHORIZED`.
