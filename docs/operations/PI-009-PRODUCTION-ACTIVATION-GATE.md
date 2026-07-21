# PI-009 Production Activation Gate

## Status

**BLOCKED BY DESIGN — EXPLICIT OPERATOR APPROVAL REQUIRED**

This document authorizes no production write, migration, scheduler
activation, retry, restore or remediation.

## Implementation Evidence

- Implementation commit:
  `e1d46099427321a3ba7a150aad589320c8f1261a`
- Targeted tests: 17 passed
- Full regression: 710 passed, 5 deselected, 427 warnings
- Production database SHA-256:
  `435857ee9e5940fc4ab18d164a63144d422955724e8c818f33529264b792663c`
- Production database modified during implementation: no
- WAL content modified during implementation: no
- Write API exposed: no
- Dashboard error policy: panel-local fail-soft

## Architecture Boundary

AIControlCenter remains the sole Control Plane.

Ubuntu remains a stateless infrastructure worker and owns no PI-009
business logic, policy, orchestration or application state.

## Mandatory Approval Gates

- [ ] Architecture review approved.
- [ ] Migration command reviewed in read-only dry-run form.
- [ ] Current production backup verified.
- [ ] Restore procedure reviewed without execution.
- [ ] Scheduler job identifiers and cadence approved.
- [ ] Missed-run and freshness thresholds approved.
- [ ] Notification and escalation destinations approved.
- [ ] Rollback owner assigned.
- [ ] Observation window assigned.
- [ ] Explicit production activation approval recorded.
- [ ] Notion synchronization completed.

## Activation Sequence

1. Reconfirm Git clean and approved commit.
2. Reconfirm full regression result.
3. Reconfirm production database backup.
4. Capture database and WAL content hashes.
5. Apply only the approved migration.
6. Validate schema and append-only triggers.
7. Execute one manually authorized operation.
8. Validate API and Dashboard projections.
9. Activate scheduler only after manual validation.
10. Observe health, missed-run and notification behavior.
11. Record evidence in CHANGELOG, MASTER, ROADMAP and Notion.

## Immediate Stop Conditions

Stop activation when any of the following occurs:

- unexpected production database hash change;
- non-empty or unexplained WAL growth;
- failed schema validation;
- write method exposed through the API;
- Dashboard exception escaping its panel boundary;
- automatic retry, restore or remediation observed;
- scheduler ownership outside AIControlCenter;
- Git status not clean;
- rollback evidence unavailable.

## Rollback Boundary

Rollback must be explicitly authorized.

No automatic restore, database replacement, WAL deletion, checkpoint,
retry or catch-up is permitted.
