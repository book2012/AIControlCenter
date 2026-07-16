# PI-001 Mac Dashboard Shadow API Integration

## Status

In Progress

## Scope

- Connect the Mac Dashboard to the local Shadow API.
- Read-only HTTP GET requests only.
- Display health and runtime commit validation.
- Do not connect directly to the Ubuntu Worker.

## Production Constraints

- AIControlCenter remains the single Control Plane.
- Dashboard must remain operational when Ubuntu is offline.
- No write operations are permitted in this feature.

## Production Gate Result

Status: COMPLETE

Production validation date: 2026-07-16

Runtime commit:

`ba8d2c9772577863c3c040d01654c4f011e2d45e`

Runtime short commit:

`ba8d2c977257`

### Operational Validation

- Health endpoint: HTTP 200
- Dashboard endpoint: HTTP 200
- Dashboard write probe: HTTP 405
- Shadow mode: read-only
- Listener: `127.0.0.1:18100`
- Runtime metadata: available
- Runtime commit matches Git HEAD
- Runtime metadata schema: version 1
- Runtime metadata mode: shadow
- Runtime activation is gated by metadata validation
- Ubuntu infrastructure was not modified
- LaunchDaemon uses the commit-specific Mac runtime

### Architecture Outcome

The Dashboard now exposes Control Plane status through a read-only JSON contract.

Runtime identity is loaded from immutable runtime metadata. Git, launchctl and shell commands are not executed during Dashboard requests.

Runtime metadata is generated during the runtime build and validated before the `runtime/current` symlink is activated.

### Evidence

- `docs/evidence/pi-001/production-gate.txt`
- `docs/evidence/pi-001/final-test.log`
