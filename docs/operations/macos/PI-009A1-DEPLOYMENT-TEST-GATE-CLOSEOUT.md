# PI-009A1 Deployment Test Gate Closeout

Status: COMPLETE

Production authorized: NO

## Purpose

PI-009A1 repaired the deployment regression gate discovered during the
PI-009 Technical Production Authorization Review.

The work remained repository-local and did not modify the active Runtime,
launchd service, Caddy, Ubuntu, public exposure, or Production authorization.

## Initial PI-009 Result

The initial deployment regression produced:

- 1032 passed
- 18 failed
- 17 errors

The active shadow Runtime remained operational throughout the investigation.

## Root Cause 1 — Activation Inspector Dependency Classification

The ACTIVATION-01B `core.deployment.activation_inspector` package had not
been registered in the deployment dependency-boundary architecture.

This caused DPL-ZONE-001 findings which propagated into tests that require
the global dependency-boundary report to PASS.

Repair:

- added the `activation_inspector` architecture zone
- added the corresponding schema enum
- restricted allowed dependencies to:
  - activation_inspector
  - contracts
  - git_readonly_evidence

## Root Cause 2 — Package Relative Import Analysis

The dependency analyzer evaluated relative imports in package
`__init__.py` files using the package module instead of package
`__init__` import context.

For example:

`from .ports import ...`

inside:

`core.deployment.activation_inspector.__init__`

was incorrectly interpreted as:

`core.deployment.ports`

instead of:

`core.deployment.activation_inspector.ports`.

The analyzer now uses package-aware relative-import context.

This also exposed an existing legitimate read-only re-export:

`core.deployment.ports -> core.deployment.ports.audit`

The policy now explicitly permits:

`read_ports -> audit_evidence`.

## Root Cause 3 — macOS Temporary Path Canonicalization

The operational execution tests require exact test-home binding.

macOS temporary paths returned by `mktemp` used:

`/var/folders/...`

while Python `Path.resolve()` canonicalized the same location to:

`/private/var/folders/...`.

This caused:

`TEST_HOME_BINDING_INVALID`.

The reusable deployment regression runner now canonicalizes its temporary
root before exporting test environment paths.

## Root Cause 4 — Controlled Bootstrap Private-Tmp Confinement

The controlled bootstrap executor deliberately requires test roots below:

`/private/tmp/`

The first reusable runner used the normal macOS temporary directory under
`/private/var/folders/...`, causing:

`TEST_ROOT_NOT_PRIVATE_TMP`.

The runner now creates its isolated harness under `/private/tmp/` and
verifies that the canonical root remains inside that boundary.

The production safety restriction itself was not weakened.

## Final Validation

Final full deployment regression:

`1133 passed, 9 warnings in 148.38s`

Result:

PASS

The warnings are deprecation warnings and did not fail the gate.

## Repair Commit

`fe0e89af58c28d8b72b47c4c4e2f8fa86cc5739c`

Subject:

`fix(deployment): repair PI-009 dependency test gate`

## Safety Result

- Runtime pointer changes: 0
- Service mutations: 0
- Rollback executions: 0
- Caddy changes: 0
- Public openings: 0
- Ubuntu changes: 0
- Production authorized: NO

## Remaining Production Blocker

`RUNTIME_SOURCE_ISOLATION`

The active runtime venv does not contain the AIControlCenter application
source.

A neutral Candidate interpreter cannot import:

`core.api.shadow`

The current service wrapper obtains application source from the mutable
repository working tree.

Therefore runtime dependency identity and application-source identity are
not yet a single immutable production artifact.

PI-009A2 must remove repository-source dependence before Production
authorization review can complete.
