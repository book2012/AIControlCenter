# DPL-02B — Read-only Mac Control Plane Inventory

## Status and ownership

DPL-02B is ready for review. It adds a deterministic, schema-valid inventory
layer for the canonical `mac-standalone-production` profile. AIControlCenter
owns inventory composition and policy interpretation. The Mac mini M4 remains
the Brain, always-on host, and single Control Plane.

The inventory represents Git identity, runtime metadata, the production
profile, launchd desired and observed state, Host Caddy, the Colima commerce
contract, Compose desired state, WordPress, WooCommerce, and public-edge
policy. Ubuntu is neither inspected nor adapted. Optional Ubuntu observation
remains deferred.

## Boundaries

- `core/deployment/application` composes component observations, applies the
  status model, orders components, and validates the final DPL v1 payload.
- `core/deployment/ports` contains capability-specific read-only protocols for
  Git, runtime metadata, launchd, Caddy, Colima, Compose, repository file
  content, and time. There is no generic command execution port.
- `core/deployment/adapters/macos` parses repository-owned JSON, YAML,
  Caddyfile, plist, Git reference, and supplied launchd snapshot data.
  Parsing is separate from launchd observation transport.
- `core/deployment/contracts` remains the versioned JSON boundary. The
  InventoryResult item was extended compatibly with component type, details,
  evidence, structured errors, and degraded/unavailable states.

Application code imports no subprocess, socket, HTTP, or SSH dependency.
Adapters import no mutating launchd, bootstrap, install, update, rollback, or
remote executor. DPL-02B exposes no API route.

## Component status model

`present` means the supplied desired-state or observation data parsed and met
the component policy. `absent` and `unknown` remain valid contract states.
`degraded` means useful component data exists but an observation or policy
assertion is incomplete. `unavailable` means a source could not provide safe,
well-formed data.

Component failures are isolated. The collector returns a structured,
schema-valid unavailable item and continues composing other components.
Implementation exception text is not returned.

## Evidence and redaction

Evidence contains only a kind and repository-relative reference. Raw file
content, process output, absolute user paths, environment values, and
credentials are excluded. Adapter errors cross the application boundary only
as stable codes and controlled messages. Existing DPL validation continues to
reject embedded values in secret-bearing fields and unsafe relative paths.

The repository reader rejects absolute paths, parent traversal, and resolved
paths outside its configured root. Input mappings are deep-copied before
composition and are not mutated.

## Public-edge inventory rules

Host Caddy is recorded as the sole public edge. Its desired upstreams must be
loopback addresses. The Colima contract must assign public ingress to
`host-caddy`, prohibit Ubuntu and AI workloads, and bind WordPress to
loopback. Compose desired state must expose WordPress only through loopback
and use internal container networking where declared.

WordPress is recorded as the CMS Engine and WooCommerce as the Commerce
Engine. Both remain behind Host Caddy; AIControlCenter remains the
business-logic owner. Direct public application ports are prohibited.
DPL-02B records repository desired-state evidence only and performs no live
network readiness test.

## Exclusions and remaining work

DPL-02B does not activate, install, bootstrap, restart, reload, update, or
roll back any runtime. It does not execute launchctl, Caddy, Docker, Compose,
network, SSH, production, or Ubuntu operations. It does not alter runtime,
launchd, Caddy, Colima, or Compose configuration.

DPL-02C remains responsible for the next read-only deployment-package
application capability defined by the program plan. DPL-02D remains
responsible for GET-only API composition. Neither desired-state inventory nor
a deployment package grants production activation authority. DPL-02 remains
open.
