# AI Home Datacenter Architecture

## Platform Goal

AI Home Datacenter is a production-ready,
multi-year AI platform rather than a conventional
home server.

## Mac mini M4 — Control Plane

The Mac mini is the always-on Brain and the single
AIControlCenter Control Plane.

It owns:

- AI orchestration and agents
- business logic and workflow orchestration
- Dashboard and Homepage
- WordPress and WooCommerce headless integration
- n8n automation
- scheduling and notifications
- GitHub, Notion, and Ubuntu control
- AI product and customer workflows

## Ubuntu Server — Infrastructure Worker

Ubuntu is an on-demand, stateless infrastructure
worker.

It provides:

- Docker and container runtime
- storage and file operations
- Immich, Nextcloud, and Plex
- backups
- infrastructure JSON APIs

Ubuntu must not own AI workloads, business logic,
Control Plane orchestration, or application state.

## Architecture Principles

- Git First
- JSON First
- REST and headless architecture
- Docker Compose and Infrastructure as Code
- read-only monitoring before write operations
- stateless infrastructure workers
- modular services
- automated testing and documentation
- rollback before cutover

## Current Runtime Architecture

The Mac Shadow API is supervised by a system
LaunchDaemon.

- Service: system/com.aicontrolcenter.api.shadow
- Application user: kyouhan
- Listener: 127.0.0.1:18100
- Mode: shadow-read-only
- Runtime: commit-specific Python virtual environment
- GUI login required: false
- Mutating HTTP methods: blocked

## Production Gate

Ubuntu AIControlCenter remains active until:

- Headless Reboot Recovery passes
- 24-hour Shadow observation passes
- Ubuntu Worker JSON integration passes
- Cutover and rollback validation pass

<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:START -->
## ADR: Headless Mac Control Plane Supervisor

            **Status:** Accepted

            ### Decision

            AIControlCenter Shadow Runtime is supervised
            by a system LaunchDaemon.

            The LaunchDaemon plist and installed runner
            are owned by `root:wheel`, while the Python
            application runs as `kyouhan`.

            ### Runtime Flow

            `system launchd`
            → `non-root runner`
            → `commit-specific Python runtime`
            → `core.api.shadow:app`
            → `127.0.0.1:18100`

            ### Security Boundaries

            - GUI login is not required.
            - The application process must not run as root.
            - The API listens only on localhost.
            - GET, HEAD, and OPTIONS are allowed.
            - Mutating HTTP methods are blocked.
            - Git HEAD and Runtime commit must match.
            - A dirty Git repository prevents restart.
            - Ubuntu remains an infrastructure worker.
            - Business logic remains on the Mac Control Plane.

            ### Rejected Alternative

            A user LaunchAgent was rejected for production
            because it requires an active GUI login domain
            and failed the headless reboot recovery test.

            ### Verified Gate

            - LaunchDaemon loaded: passed
            - Non-root process: passed
            - Health HTTP `200`: passed
            - Write probe HTTP `405`: passed
            - Localhost-only listener: passed
            - Automatic restart: `1661 → 1975`

            - Generated: `2026-07-14T03:31:53+00:00`
- Branch: `sprint/mac-control-plane-foundation`
- Commit: `db4d93a2652a704dfa9a7e149623064adb961504`
- Runtime commit: `db4d93a2652a`
<!-- AICONTROLCENTER:MAC_SHADOW_DAEMON:END -->

<!-- AICONTROLCENTER:HEADLESS_REBOOT_RECOVERY:START -->
## ADR: Headless LaunchDaemon Recovery

            **Status:** Accepted and operationally verified.

            AIControlCenter uses a system LaunchDaemon
            as its Mac Control Plane supervisor.

            The plist and runner are root-owned, while
            the application process runs as `kyouhan`.

            Runtime startup does not depend on:

            - a GUI login
            - GitHub availability
            - an SSH agent
            - the Ubuntu Worker

            Operational logs use:

            `/var/log/aicontrolcenter`

            The API remains localhost-only and blocks
            mutating HTTP requests during Shadow Mode.

            Infrastructure-as-Code reconciliation of
            the manager installer remains required.

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
## Shadow Observation Architecture

A separate non-root system LaunchDaemon observes the
AIControlCenter Shadow API.

The observer performs read-only validation and does not
own scheduling, business logic, application state, or
Ubuntu infrastructure state.

- Observer:
  `com.aicontrolcenter.api.shadow.observer`
- User: `kyouhan`
- Interval: `300 seconds`
- Data format: `JSON Lines`
- Configured: `2026-07-14T04:19:41+00:00`
<!-- AICONTROLCENTER:SHADOW_OBSERVATION:END -->
