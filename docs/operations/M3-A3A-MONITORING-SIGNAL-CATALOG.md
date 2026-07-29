# M3-A3A Monitoring Signal Catalog

Status: `CLOSED`

| Dimension | Primary evidence | Healthy/allowed signal | Alert-candidate conditions |
| --- | --- | --- | --- |
| CONTROL_PLANE | Explicit owner | AIControlCenter/Mac | Missing or Ubuntu ownership |
| AUDIT_INTEGRITY | Read-only report ID/digest, schema, chain, violations | Valid and contradiction-free | Missing/stale evidence, invalid schema or chain |
| AUDIT_RECOVERY | Recovery report/digest, backup and drill ages | Valid within configured ages | Missing, stale or critical-age evidence |
| REPLAY_INTEGRITY | Read-only report, schema, chain, lifecycle, violations | Valid and contradiction-free | Invalid chain or lifecycle; missing/stale evidence |
| REPLAY_RECOVERY | Recovery report, restored states/protection, ages | Valid and restored | Replay protection failure; stale backup/drill |
| REPLAY_CONCURRENCY | Explicit post-recovery result | Valid | Missing or failed result |
| DEPLOYMENT_READINESS | M2 readiness and pilot closeout | READY and CLOSED | Missing or contradictory evidence |
| TEST_HEALTH | Passed, failed, deselected, warnings | Failures within tolerance | Failure; warnings degrade when configured |
| GIT_HEALTH | Clean, ahead, behind | Clean and within zero-default tolerance | Dirty, ahead or behind |
| SAFETY | Complete deployment counter set | Every counter zero | Any nonzero counter |
| DOCUMENTATION | Explicit completion evidence | Complete | Incomplete |
| PRODUCTION_AUTHORIZATION | Explicit authorization flag | `false` in PRE_ACTIVATION | Any `true` contradiction |

Statuses are `HEALTHY`, `DEGRADED`, `UNAVAILABLE`, `BLOCKED`, `CRITICAL` and
`NOT_CONFIGURED_ALLOWED`. Severity is `INFO`, `WARNING` or `CRITICAL`. Overall
status is the deterministic strongest result: critical, blocked, unavailable,
degraded, then healthy/allowed.

Expected inactive databases, writers, schedules and production authorization
are PRE_ACTIVATION restrictions. They never represent production health.
Candidates are never dispatched, and no credentials, raw payloads, database
paths, nonces, environment variables, commands or authorization headers are
accepted as monitoring evidence.
