# M3-A3B Alert Routing Policy

INFO routes to `CONTROL_PLANE_DASHBOARD`. WARNING additionally routes to
`OPERATOR_REVIEW_QUEUE`. CRITICAL additionally routes, in stable policy order,
to `INCIDENT_RESPONSE_QUEUE`. Safety and production-authorization conditions
may add `SECURITY_REVIEW_QUEUE`; documentation findings may add
`DOCUMENTATION_BACKLOG`.

Matching history inside cooldown is suppressed. Severity increases bypass
cooldown and escalate immediately. WARNING and CRITICAL reminders route after
their configured intervals. Resolved conditions without a new occurrence are
suppressed; reappearing evidence routes as recurrence, and critical recurrence
escalates.

History is immutable caller-supplied evidence. Conflicts, future timestamps,
malformed bindings, authorization contradictions, arbitrary destinations,
adapters and dispatch requests block routing. Stale history is ignored under
the explicit maximum-age policy. No database or system clock is consulted.

Escalation levels are logical policy results only: `NONE`, `OPERATOR_REVIEW`,
`INCIDENT_RESPONSE` and `SECURITY_REVIEW`. No external escalation system is
implemented or invoked.
