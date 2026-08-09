# PI-009 Production Activation Gate

<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:START -->
## ACTIVATION-01C Authorization Contract

Status: `FROZEN`

Active Runtime: `b9ad351a7241`

Candidate Runtime: `acd80ab9f6ae`

Candidate source commit: `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

Candidate startup import gate: `PASS`

Observed Active Runtime failure:

`ModuleNotFoundError: No module named 'jsonschema'`

First mutation boundary:

`Runtime pointer activation only`

Explicit service restart authority:

`NO`

Automatic rollback authority:

`NO`

Ubuntu changes:

`NO`

Public opening:

`NO`

Production authorization:

`NO`

Canonical human approval statement:

`ACTIVATION-01C AUTHORIZE POINTER SWITCH acd80ab9f6ae FROM b9ad351a7241`

The exact mutation command and rollback boundary are defined in:

- `docs/deployment/ACTIVATION-01C-CONTROLLED-ACTIVATION-ARCHITECTURE.md`
- `docs/operations/macos/ACTIVATION-01C-HUMAN-AUTHORIZATION-CONTRACT.md`
<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:END -->

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

## PI-009A1 Test Gate Result

PI-009A1 deployment regression repair is COMPLETE.

Final test result:

`1133 passed, 9 warnings`

Implementation commit:

`fe0e89af58c28d8b72b47c4c4e2f8fa86cc5739c`

The dependency-policy and test-harness blockers are closed.

Production authorization remains blocked by:

`RUNTIME_SOURCE_ISOLATION`

The current production wrapper obtains AIControlCenter application source from
the mutable repository working tree. PI-009A2 must establish immutable source
identity before Production authorization can proceed.

## PI-009A2 Runtime Source Isolation Architecture

The Production source-isolation repair uses:

`runtime/venvs/<runtime-id>`

paired with:

`runtime/sources/<runtime-id>`

The source artifact is an immutable tracked Git snapshot of the exact full
source commit recorded by the Runtime.

The existing Runtime current pointer is preserved.

Source artifact creation and wrapper cutover are separate explicit human
authorization gates.

Production remains unauthorized until the wrapper executes the application
from the immutable source artifact and loaded-source identity is verified.

## PI-009A2 Application State Isolation Gate

Production Runtime source and writable application state must be separate.

Required:

- application source is immutable
- `AICONTROLCENTER_DATA_ROOT` is an absolute external data root in production
- conversation SQLite state is outside the source artifact
- scheduler SQLite state is outside the source artifact
- no Runtime source file or directory becomes writable to accommodate state
- source and state isolation both pass before wrapper cutover

The former Candidate `acd80ab9f6ae` does not satisfy this source version of the
state-isolation contract.

A new Candidate is required.

Production remains unauthorized.

## PI-009A2 A2.2A Gate Result

Status:

VALIDATED

Runtime Candidate:

`7b171f135dc7`

Source commit:

`7b171f135dc7882546bf7f733208778f1aef4943`

Canonical build report SHA-256:

`61f88c861a4ecf44a17570e46dc1608866193b987c0448e8eca747d294dfa77b`

Required checks passed:

- canonical build exactly once
- dependency installation
- application import
- canonical test suite
- Runtime marker identity
- Runtime metadata identity
- pip check
- temporary immutable source execution
- external writable state isolation
- active Runtime unchanged
- service unchanged
- HTTP 200 / 200 / 405
- Git clean

Operational source artifact creation remains a separate authorization gate.

Production remains NOT_AUTHORIZED.

## PI-009A2 A2.2B Gate Result

Status:

VALIDATED

Runtime/source pair:

`7b171f135dc7`

Source commit:

`7b171f135dc7882546bf7f733208778f1aef4943`

Manifest SHA-256:

`a74977db05ac93bfc5c9e3d621d0748822c5f7f6021f7f0d0fb7c2d3f1983626`

Required checks passed:

- source artifact builder exactly once
- source validator
- manifest identity
- Runtime/source identity
- source immutability
- Git metadata absence
- required Runtime assets
- immutable-source application execution
- external writable application state
- active Runtime unchanged
- live wrapper unchanged
- service unchanged
- HTTP 200 / 200 / 405
- Git clean

A2.3 live cutover requires separate human authorization.

Production remains NOT_AUTHORIZED.
