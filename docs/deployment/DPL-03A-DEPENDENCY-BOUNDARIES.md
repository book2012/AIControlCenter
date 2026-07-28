# DPL-03A Dependency Boundaries

Status: ready for review. DPL-03 is not complete.

## Responsibility boundaries

The DPL dependency graph is intentionally one-way. Contracts define immutable
data. Read ports define observation capabilities using contracts and pure
types. Read adapters implement those ports. Read application services compose
only contracts and ports. Plan services may consume contracts and read-result
models, but cannot reach executors. Apply services are a separate future
boundary and are absent from default API composition.

The deployment API may compose read and plan application services. It must not
import apply, worker, SSH, generic command, launchd mutation, Caddy mutation or
Compose mutation modules. Worker infrastructure is optional and stateless; it
is not reachable from DPL read or plan composition. AIControlCenter on the Mac
mini remains the single Control Plane and host Caddy remains the sole public
edge. WordPress and WooCommerce remain engines; platform business logic remains
owned by AIControlCenter.

## Machine enforcement

`config/deployment/dependency-boundaries.json` is the repository-owned,
versioned policy. `DependencyBoundaryPolicy` and `DependencyBoundaryReport`
are strict DPL v1 JSON Schema contracts. Unknown fields are rejected, including
unknown security-sensitive fields. The canonical JSON SHA-256 digest identifies
the exact policy used for each report.

`validate_dependency_boundaries` accepts only repository-relative POSIX paths,
rejects absolute and traversing paths, reads Python source, and parses it with
Python's AST. It inspects `Import` and `ImportFrom` nodes without importing
analyzed modules. Deterministic sorting covers inputs, classifications, allowed
imports, violations, warnings and quarantine findings.

AST validation is authoritative because grep cannot distinguish syntax from
comments, docstrings, assertion strings or ordinary method calls. For example,
the validator ignores the text `UbuntuWorkerClient` in a test string and does
not confuse `ConfigLoader.load()` with `launchctl load`. It detects actual
imports and imported prohibited symbols.

The service performs no shell execution, subprocess invocation, dynamic import,
network access, secret-file discovery or persistent evidence write.

## Legacy quarantine

The policy narrowly classifies the existing pre-DPL manifest, inspector, diff,
plan, dry-run, approval and execution-gate modules as `LEGACY_UNSUPPORTED`.
Quarantine records a reason, empty allowed-consumer list, prohibited consumers,
migration target, review date and `production_authorized=false`. It documents
existing risk; it cannot authorize a dependency. Read, plan and API zones remain
forbidden from importing quarantined modules.

The legacy inspector's `launchctl print` subprocess observation is reported as
a quarantine finding. DPL-03A does not delete, move, refactor or make that
module reachable from the DPL API.

## Authorization and exclusions

The policy has authorization effect `NONE`. Every report fixes
`production_authorized=false`, `production_writes=0` and `ubuntu_changes=0`.
A desired-state package remains data, not activation authorization.

DPL-03A adds no HTTP route, CLI, executor, deployment behavior, production
evidence, audit database write or runtime integration. It does not complete
DPL-03.

## Next step

DPL-03B should compose pure plan services over the enforced contracts and
read-result models. Any future apply work requires a separate task, explicit
authorization, and composition that remains absent from the default API.
