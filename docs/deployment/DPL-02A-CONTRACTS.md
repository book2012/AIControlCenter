# DPL-02A — DPL v1 Contract Layer

## Ownership and scope

`core/deployment/contracts` is the AIControlCenter-owned boundary for the
versioned DPL v1 JSON contract. It is pure, local, read-only code. It does not
inspect hosts, symlinks, Caddy, Compose, Colima, services, or the network, and
it does not invoke subprocesses.

The contract layer defines immutable deployment packages, inventory results,
validation reports, desired/current diffs, deterministic dry-run plans,
readiness reports, and error envelopes. Apply and execution contracts are
deliberately excluded. A package is desired state, never activation authority.

## Registry and identity

The registry at `schemas/v1/registry.json` binds stable contract names to
Draft 2020-12 schemas and `urn:aicontrolcenter:dpl:contract:v1:*` identifiers.
Reference resolution is local-only. Every payload declares
`schema_version: dpl/v1`; unknown contract names and versions fail closed.

A package identifies its package ID and semantic version, UTC creation time,
source repository, exact lowercase 40-character Git commit, source branch,
canonical target, components, policy declarations, and artifact digest.
The only Control Plane target is macOS / `control-plane` /
`mac-standalone-production`. Ubuntu is representable only as an optional
`observation-target`.

## Immutability and canonicalization

`canonical_json_bytes` serializes JSON deterministically with sorted object
keys, compact separators, explicit UTF-8, and no insignificant whitespace.
NaN and Infinity fail validation. `sha256_digest` returns lowercase
`sha256:<64 hex>` identity, and `verify_digest` uses constant-time comparison
to detect changed content. These operations do not mutate callers' objects.

Artifact references are content-addressed. Component image references, when
present, must use an `@sha256:` digest; mutable tags alone are rejected.
Package-relative paths reject absolute paths and parent traversal.

## Read-only and edge policy

Every contract is `read_only: true`. Dry-run plans additionally require
`execution_enabled: false` and allow observation verbs only. Apply, execute,
install, restart, and bootstrap operations are rejected by pure validation.
Production activation and writes remain prohibited.

Host Caddy is the sole public-edge owner. Direct public application ports are
prohibited. These declarations are contract assertions only; DPL-02A performs
no live edge or runtime inspection.

Security-sensitive objects reject unknown fields. Validation also rejects
non-empty fields named `password`, `token`, `secret`, `private_key`, or
`credential` at any nesting level.

## Compatibility

The DPL v1 layer is additive and does not change the existing
`core/deployment` 1.0 manifest, plan, diff, dry-run, approval, or response
contracts. Future integration should use explicit adapters rather than
silently changing those public shapes. DPL-02A provides contracts only; apply,
activation, runtime access, and compatibility adapters remain separate work.
