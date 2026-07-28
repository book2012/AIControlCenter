# ADR: DPL Deployment Package Boundary

Date: 2026-07-28

Status: Accepted

Decision scope: DPL v1

## Context

AIControlCenter needs a deployment package contract without allowing package
inspection or planning to become production execution. Existing deployment,
remote-worker and platform-specific artifacts contain both read and mutation
surfaces, and Mac inspection includes inherited Linux assumptions.

## Decision

AIControlCenter owns DPL governance, policy, orchestration, approval,
authorization, audit and deployment control. The Mac mini M4 is the always-on
Brain and single Control Plane.

DPL v1 is an immutable desired-state and observation contract defined by
versioned JSON Schemas and a registry. It is JSON-first, read-only-first and
Git-first. Package identity and observations are auditable; a package never
constitutes authority to execute.

The architecture has three strict boundaries:

1. Read observes inventory and current state without mutation.
2. Plan validates policy, computes diff and produces a dry-run plan without
   importing or invoking apply executors.
3. Apply is a separate future boundary requiring explicit authorization. It is
   absent from DPL-02.

Production writes and production activation are not authorized.

## Platform Boundary

Mac production services use `launchd`. Host Caddy is the only public edge and
owns transport ingress, not business logic. WordPress is the CMS Engine,
WooCommerce is the Commerce Engine, and AIControlCenter owns all business logic.
Caddy, Colima, Compose and the Commerce host port require one canonical ingress
contract with end-to-end validation in DPL-02.

Ubuntu is optional, stateless and on demand. It must not own AI workloads,
business logic, application state, governance, approval, authorization or
orchestration. DPL-02 must not activate an Ubuntu adapter, and
`UbuntuWorkerClient.execute` is excluded from DPL.

## Ubuntu Action Policy

Future fixed typed read-only actions may be limited to:

- `worker.health.read`
- `worker.inventory.read`
- `worker.services.read`
- `worker.storage.read`
- `worker.backup_status.read`
- `worker.power_state.read`

Free-form or mutating actions are prohibited:

- `worker.command.execute`
- `worker.shell.execute`
- `worker.service.restart`
- `worker.compose.apply`
- `worker.file.write`

`SSHRunner` can be evaluated later only as an implementation detail behind the
typed read-only allowlist. No generic command parameter may cross the DPL
boundary.

## Legacy Linux Policy

Linux systemd Control Plane artifacts are classified `LEGACY_UNSUPPORTED`.
They are production-prohibited and excluded from DPL. DPL-01 preserves them in
place for historical traceability; it does not move, delete or activate them.

## Consequences

- DPL-02 can inventory, validate manifests and policy, diff, dry-run, report
  readiness and audit.
- DPL-02 cannot apply, install, restart, bootstrap, execute rollback, write to
  production or execute generic Ubuntu commands.
- Read/plan code cannot depend on apply executors.
- Platform-specific observations must normalize into versioned reports without
  moving platform ownership away from AIControlCenter.
- Any activation or mutation requires a later, explicit architecture and
  production authorization gate.
