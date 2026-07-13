# launchd Shadow Runtime Supervisor

## Purpose

Run the validated AIControlCenter runtime as a user-scoped,
localhost-only, read-only Shadow Control Plane.

## Service

- Label: com.aicontrolcenter.api.shadow
- Host: 127.0.0.1
- Port: 18100
- Runtime: commit-specific current venv
- Mode: shadow-read-only

## Safety

The Shadow API:

- permits GET, HEAD, and OPTIONS
- blocks mutating HTTP methods
- does not replace the Ubuntu Control Plane
- does not migrate secrets
- does not connect Dashboard or n8n
- does not expose a public listener

## Install

    python3.12 \
      ops/macos/launchd/manage-shadow-agent.py \
      install

## Status

    python3.12 \
      ops/macos/launchd/manage-shadow-agent.py \
      status

## Rollback

    python3.12 \
      ops/macos/launchd/manage-shadow-agent.py \
      uninstall

## Production Gate

The following field must be true:

    .shadow_supervisor_gate_passed
