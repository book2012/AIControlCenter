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

The operator must preserve a non-repository sandbox root, Mac Control Plane
ownership, zero Ubuntu/runtime/network/production activity, and zero real
executor invocations. Persistent SQLite audit must be implemented and
separately authorized before any broader mutable deployment.
