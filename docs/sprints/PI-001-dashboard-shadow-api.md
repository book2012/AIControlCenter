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
