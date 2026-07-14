# LaunchDaemon Shadow Supervisor

## Purpose

Run the AIControlCenter Shadow API without requiring a GUI login.

## Architecture

- System supervisor: launchd
- Scope: LaunchDaemon
- Application user: kyouhan
- Application group: staff
- Root application process: prohibited
- Host: 127.0.0.1
- Port: 18100
- Mode: shadow-read-only

## Installation

Refresh sudo credentials:

    sudo -v

Install:

    python3.12 \
      ops/macos/launchd/manage-shadow-daemon.py \
      install

## Status

    python3.12 \
      ops/macos/launchd/manage-shadow-daemon.py \
      status

## Rollback

Refresh sudo credentials:

    sudo -v

Uninstall:

    python3.12 \
      ops/macos/launchd/manage-shadow-daemon.py \
      uninstall

## Production Gate

The following field must be true:

    .shadow_daemon_gate_passed

## Safety

- The plist and installed runner are root-owned.
- The application process runs as kyouhan.
- The API binds only to localhost.
- Mutating HTTP methods remain blocked.
- Ubuntu is not modified.
- Secrets are not migrated.
