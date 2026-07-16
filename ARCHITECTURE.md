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

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## ADR: Mac Control Plane Production Baseline

**Status:** Accepted and operationally verified.

The Mac mini M4 is the sole AIControlCenter
Control Plane.

Ubuntu remains a stateless infrastructure worker.

Runtime flow:

`system launchd`
→ `root-owned runner`
→ `non-root application user`
→ `commit-specific Python runtime`
→ `AIControlCenter Shadow API`
→ `127.0.0.1:18100`

Validated contracts:

- Repository commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- GUI login dependency: none
- Transactional install: enabled
- Transactional rollback: enabled
- launchd settle after bootout: 2 seconds
- Final restart PID: `19761 → 19842`

Ownership boundaries:

- Mac owns AI, orchestration, business logic,
  scheduling, workflow and application state.
- Ubuntu owns Docker, storage, backup and file
  operations only.
- Ubuntu must not own AI workloads, business
  logic, Control Plane orchestration or
  application state.
- Infrastructure is consumed through JSON APIs.
- Production writes remain disabled until a
  separate cutover Gate is approved.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->
