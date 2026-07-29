# M3 Permit Replay State Machine

The append-only state machine is:

`UNUSED → RESERVED → CONSUMED`

or:

`UNUSED → RESERVED → FAILED_CLOSED`

`RESERVED` is required before controlled executor work. `CONSUMED` and
`FAILED_CLOSED` are terminal and mutually exclusive. A terminal event without
a reservation, a second reservation, a second terminal event, or any changed
permit, activation, target or environment binding is denied.

An identical retry returns the durable existing event as an idempotent receipt
without appending. A conflicting retry is denied. If state cannot be inspected
or recorded with certainty, the result is default deny; it never reports the
permit reusable.

Each global ledger event has a unique monotonic sequence and event ID. Its hash
binds the canonical payload digest and previous event hash. Every write first
validates the entire ledger and all permit lifecycles. Invalid state is never
repaired.

AIControlCenter on the Mac Control Plane owns this state. Ubuntu owns no permit,
nonce or replay state. Raw nonce values are never persisted. Production
activation is `NOT_AUTHORIZED`.
