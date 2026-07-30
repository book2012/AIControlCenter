# M3-A4B2B1B Execution Window Policy

An effective window requires explicit timezone-aware approval, issuance,
not-before, expiry and bootstrap-deadline timestamps. Domain logic receives
these values as input and never reads the system clock.

The timestamps must satisfy:

`approval <= issuance <= not-before < bootstrap deadline <= expiry`

The approval-to-issuance delay, permit TTL, issuance-to-claim delay and maximum
execution duration must be positive and bounded. Maximum uses is exactly one.
A proposed window is not effective until every human-approval gate passes.
Expired, missing or contradictory windows fail closed.

The current proposal was 2026-07-30 11:00–11:20 +09:00. It has no effective
window because the independent approver, approval and restriction
acknowledgement are absent. Production remains `NOT_AUTHORIZED`.
