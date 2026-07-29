# M3-A3C Monitoring and Alert Drill Runbook

1. Confirm non-production scope, explicit timestamps, immutable evidence and
   history, bounded configuration, allowed logical routes, and
   `production_authorized=false`.
2. Instantiate a new `InMemorySimulatedAlertSink`; never reuse a global sink or
   provide an external adapter.
3. Run `MonitoringAlertDrillService` with one named supported scenario.
4. Require a deterministic snapshot, routing plan, drill plan, envelope order,
   receipt order, and validation report.
5. Require exact candidate, routed, escalated, suppressed, blocked, envelope,
   and receipt counts.
6. Require every receipt to bind exactly once and claim zero dispatch,
   delivery, persistence, and network use.
7. Treat `BLOCKED` or `FAILED` as terminal. Never retry through a real adapter.

Supported scenarios are the nineteen values in
`MonitoringAlertDrillScenario`, covering healthy, warning, duplicate,
reminder, escalation, recurrence, audit/replay, safety, authorization, Ubuntu,
Git, regression, missing-evidence, tamper, and controlled-sink-failure paths.
