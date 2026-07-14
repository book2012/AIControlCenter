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

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## Validated Runtime Status

            - Gate:
              `shadow_daemon_gate_passed=true`
            - Service:
              `system/com.aicontrolcenter.api.shadow`
            - Process user: `kyouhan`
            - Runtime:
              `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/0f1b4c5d8aba`
            - Listener: `127.0.0.1:18100`
            - Health: HTTP `200`
            - Mutating request probe: HTTP `405`
            - Automatic restart: `1661 → 1975`
            - GUI login required: `false`

            ## Listener Semantics

            During normal operation:

            - port `18100` must be listening
            - the listener PID must match the LaunchDaemon PID
            - the listener must bind only to `127.0.0.1`

            During uninstall or bootout:

            - port `18100` must be released

            An open localhost listener after an automatic
            restart is a successful recovery condition,
            not a port-release failure.

            ## Next Gate

            Headless reboot recovery must verify the service
            before any GUI login.

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->
