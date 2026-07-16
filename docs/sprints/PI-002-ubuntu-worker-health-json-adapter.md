# PI-002 Ubuntu Worker Health JSON Adapter

Status: DISCOVERY

## Goal

Consume Ubuntu worker health through a read-only JSON contract.

## Safety Constraints

- Ubuntu remains stateless.
- No AI workloads on Ubuntu.
- No business logic on Ubuntu.
- Read-only monitoring first.
- All worker status is normalized as JSON.

## Existing Architecture

- `WorkerFactory` creates `UbuntuWorkerClient` instances.
- `SSHRunner` owns remote command execution.
- `UbuntuWorkerClient.status()` consumes worker health data.
- `MonitoringSnapshot` normalizes unavailable workers.
- `DashboardAPI` exposes worker data when workers are requested.

## Target Contract

- Worker health must be valid JSON.
- SSH execution must have a bounded timeout.
- Invalid JSON must return a normalized unavailable status.
- SSH failure must not fail the Dashboard response.
- Ubuntu must remain read-only and stateless.

## Worker Health Schema v1

Required fields:

- `schema_version`: integer equal to `1`
- `worker_id`: non-empty string
- `role`: non-empty string
- `health`: normalized worker health state
- `available`: boolean

Invalid JSON, non-object payloads, missing fields and unsupported schema versions are rejected.

## SSH Transport Contract

- SSH uses non-interactive `BatchMode=yes`.
- SSH connection establishment has a bounded timeout.
- Remote command execution has a bounded subprocess timeout.
- Timeout failures are normalized as `ssh_command_timeout`.
