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

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## Headless Reboot Recovery

            The system LaunchDaemon successfully recovered
            after a full reboot without a GUI login.

            ### Lifecycle

            - `bootstrap` registers an unloaded service.
            - `kickstart` restarts a loaded service.
            - `bootout` removes the service registration.
            - Port `18100` must be open during operation.
            - Port `18100` must be released after bootout.

            ### Canonical Runtime

            - Service:
              `system/com.aicontrolcenter.api.shadow`
            - Application user: `kyouhan`
            - Listener: `127.0.0.1:18100`
            - Log directory:
              `/var/log/aicontrolcenter`
            - Allowed methods:
              `GET`, `HEAD`, `OPTIONS`
            - Mutating methods: blocked

            - Verified: `2026-07-14T04:11:33+00:00`
- Commit: `aadb42089642a17f54825b850626bd43d5e22015`
- Runtime: `/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/venvs/aadb42089642`
- Pre-reboot PID: `875`
- Post-reboot PID: `567`
- Process user: `kyouhan`
- Health HTTP: `200`
- Write probe HTTP: `405`
<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:END -->

<!-- AICONTROLCENTER:SHADOW_OBSERVATION:START -->
## Observer Integration

The main Shadow Daemon is monitored by:

`system/com.aicontrolcenter.api.shadow.observer`

The observer runs as `kyouhan` every 300 seconds and
stores JSON Lines in:

`/var/log/aicontrolcenter/shadow-observation.jsonl`

The observer is read-only and does not restart or modify
the main service.

Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->
