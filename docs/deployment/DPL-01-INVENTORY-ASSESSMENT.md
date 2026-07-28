# DPL-01 Deployment Package Inventory and Assessment

Status: COMPLETE

Program: DPL — Deployment Package

Baseline: `ba6fdb6a69ee9398b44fdd0810102b078c38c7f8`

Assessment date: 2026-07-28

Production activation: NOT AUTHORIZED

## Purpose

DPL-01 records the current deployment inventory, ownership boundaries,
architecture decisions, risks, blockers and sprint plan. It changes
documentation only. It does not activate a runtime, contact Ubuntu, create a
schema or authorize a production write.

## Canonical Ownership

| Asset or responsibility | Owner | DPL rule |
| --- | --- | --- |
| Control Plane and always-on Brain | Mac mini M4 | Single authoritative Control Plane |
| Governance, policy and authorization | AIControlCenter | Must not be delegated |
| Orchestration, approval and audit | AIControlCenter | Must not be delegated |
| Business logic and deployment control | AIControlCenter | Must not be delegated |
| Public ingress | Host Caddy on Mac | Only public edge |
| CMS records | WordPress | CMS Engine, not business-logic owner |
| Commerce records | WooCommerce | Commerce Engine, not business-logic owner |
| Optional infrastructure work | Ubuntu | Stateless and on demand |
| Desired state and observations | Versioned DPL JSON package/report | Immutable, Git-first contract |

Ubuntu must not own AI workloads, business logic, application state,
governance, approval, authorization or orchestration.

## Repository Inventory

| Area | Current artifacts | Assessment |
| --- | --- | --- |
| Deployment domain | `core/deployment/manifest.py`, `inspect.py`, `diff.py`, `plan.py`, `dry_run.py`, `approval.py`, `execution_gate.py` | Useful inventory and planning code exists, but read/plan and apply responsibilities do not yet have a strict package boundary. |
| Mac service inventory | `config/services/mac-standalone-production.json` and `config/schemas/mac-service-manifest.schema.json` | Existing manifest is Mac-oriented; it is not the canonical versioned DPL v1 package/report contract. |
| Mac runtime | `ops/macos/runtime/` | Production runtime and health inspection exist; DPL-02 may inspect but may not bootstrap or activate. |
| Mac supervision | `ops/macos/launchd/`, `deploy/launchd/`, `deploy/macos/` | `launchd` is the production service model. Install, restart, rollback and bootstrap paths are outside DPL-02. |
| Public edge | `ops/macos/caddy/Caddyfile` and Caddy LaunchDaemon plist | Host Caddy is the only public edge. Its route to the Commerce host port needs one canonical ingress contract. |
| Commerce runtime | `deploy/shopping/compose.yaml`, WordPress plugin assets and `ops/macos/colima/commerce-runtime.json` | WordPress and WooCommerce remain engines; Compose and Colima observations require end-to-end validation with Caddy. |
| Ubuntu access | `core/worker/ubuntu.py` and `core/worker/ssh_runner.py` | Generic execution remains reachable. `UbuntuWorkerClient.execute` is explicitly excluded from DPL. |
| Linux services | `deploy/systemd/` and systemd-dependent health assumptions | `LEGACY_UNSUPPORTED`; production-prohibited and excluded from DPL. Retained in place for historical documentation only. |
| Existing schemas | `config/schemas/` and domain schemas under `core/shopping/contracts/schemas/` | They do not replace a DPL v1 versioned schema registry. No DPL schemas are created in DPL-01. |

## DPL v1 Contract

A DPL v1 package is an immutable desired-state and observation contract.
Versioned JSON Schemas and a registry will define packages and reports.
Packages are JSON-first, read-only-first and Git-first. A package describes
intent; it is not an executable script and does not grant activation authority.

DPL-02 is read-only. Its allowed capabilities are:

- inventory
- manifest validation
- policy validation
- diff
- dry-run plan
- readiness reporting
- audit

DPL-02 prohibits apply, install, restart, bootstrap, rollback execution,
production writes and generic Ubuntu command execution. It must not activate an
Ubuntu adapter.

## Future Ubuntu Read-Only Action Model

The future typed allowlist is:

- `worker.health.read`
- `worker.inventory.read`
- `worker.services.read`
- `worker.storage.read`
- `worker.backup_status.read`
- `worker.power_state.read`

The following actions are explicitly prohibited:

- `worker.command.execute`
- `worker.shell.execute`
- `worker.service.restart`
- `worker.compose.apply`
- `worker.file.write`

`SSHRunner` may be considered only in a later approved sprint and only behind
fixed, typed, read-only actions. It is not an active DPL-02 adapter.

## Findings and Blockers

| ID | Severity | Finding | Required resolution |
| --- | --- | --- | --- |
| DPL-B01 | HIGH | No canonical versioned DPL JSON package/report schema | Define v1 schemas and registry in DPL-02. |
| DPL-B02 | HIGH | Generic Ubuntu remote execution remains reachable | Exclude `UbuntuWorkerClient.execute`; design deny-by-default typed boundaries. |
| DPL-B03 | HIGH | Read-only planning and mutating executors lack a strict architectural package boundary | Separate read/plan from apply packages and dependency direction. |
| DPL-B04 | MEDIUM | Mac health inspection is mixed with systemd assumptions | Make launchd the Mac production inspection contract. |
| DPL-B05 | MEDIUM | Caddy, Compose and Colima lack unified validation | Define one canonical ingress contract and validate it end to end. |
| DPL-B06 | MEDIUM | Stale SRI status remains in documentation | Supersede active SRI queues with the closed baseline and DPL program state. |

## Risks and Controls

- Capability creep could turn planning into execution. Control: no executor
  dependency from read/plan code and deny all unregistered capabilities.
- A generic SSH surface could bypass action policy. Control: no Ubuntu adapter
  in DPL-02 and no free-form command field in future contracts.
- Platform ambiguity could revive systemd as a Control Plane. Control: classify
  Linux systemd artifacts `LEGACY_UNSUPPORTED`.
- Ingress drift could expose a non-canonical service. Control: Host Caddy owns
  the public edge and DPL-02 validates Caddy through the Commerce host port.
- Mutable packages could invalidate audit evidence. Control: immutable,
  versioned JSON and Git identity.
- Documentation could imply authorization. Control: production activation and
  all production writes remain explicitly unauthorized.

## Sprint Plan

| Sprint | Outcome | Production state |
| --- | --- | --- |
| DPL-01 | Inventory, ownership, ADR, blockers and roadmap | Documentation only; complete |
| DPL-02 | Versioned package/report schemas, registry, validation, inventory, diff, dry-run, readiness and audit | Read-only; no Ubuntu adapter |
| DPL-03 | Enforce read/plan/apply package and dependency boundaries | No apply activation |
| DPL-04 | Launchd-native Mac service and health inspection | Read-only |
| DPL-05 | Canonical Caddy–Colima–Compose–Commerce ingress validation | Read-only |
| DPL-06 | Typed Ubuntu read-only action contract and policy tests | Adapter activation separately gated |
| DPL-07 | Immutable package evidence, compatibility and release-candidate validation | No production activation |
| DPL-08 | Operational readiness, regression, documentation and authorization review | Activation remains separately approved |

## DPL-01 Acceptance

- Architecture and ownership decisions are recorded.
- Six blockers are registered with required resolutions.
- SRI is treated as complete at commit
  `ba6fdb6a69ee9398b44fdd0810102b078c38c7f8`.
- The inherited regression baseline is `984 passed, 5 deselected`; it was not
  rerun because DPL-01 is documentation-only.
- No production, Ubuntu, code, configuration, schema, Compose or test change is
  authorized by this assessment.
