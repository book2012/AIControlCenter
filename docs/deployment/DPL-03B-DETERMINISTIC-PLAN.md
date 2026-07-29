# DPL-03B Deterministic Deployment Plan

## Status and ownership

DPL-03B is complete and ready for review. AIControlCenter on the Mac mini M4
owns deployment planning as part of the single Control Plane. The layer is a
pure dry-run boundary: it neither executes nor authorizes deployment.

## Inputs and outputs

`DeploymentPlanBuilder` accepts an immutable deployment package and supplied
digest, Mac inventory, ingress readiness, DPL-03A dependency-policy report,
closed target profile, and actor/context identities. Inputs are deep-copied
before composition and are never mutated.

The canonical pure-planning namespace is `core.deployment.planning`. The output
is a schema-validated `DeploymentPlanReport` containing a
`DeploymentPlan` and typed `DeploymentPlanAction` graph. Both report and plan
remain `read_only=true`, `dry_run=true`, `execution_authorized=false`,
`production_authorized=false`, `production_writes=0`, and `ubuntu_changes=0`.
No evidence is persisted.

## Deterministic identity

Canonical JSON is UTF-8, key-sorted, and serialized without insignificant
whitespace. The plan seed hashes package digest, target profile, identities,
and evidence digests. Plan and action IDs derive only from that semantic seed.
The plan digest hashes the completed semantic plan with `plan_digest` omitted.
Wall-clock time is not an input and no generated timestamp is emitted.

Identical semantic inputs therefore produce identical plan IDs, action IDs,
action order, dependency order, canonical JSON, and plan digests.

## Action graph

Actions are declarative intents only:

- `VALIDATE_PACKAGE`
- `VERIFY_DEPENDENCY_POLICY`
- `VERIFY_MAC_INVENTORY`
- `VERIFY_INGRESS_READINESS`
- `VERIFY_TARGET_PROFILE`
- `PREPARE_AUDIT_EVIDENCE`
- `REQUIRE_APPROVAL`
- `RECORD_BLOCKER`

They contain no shell, command, argv, script, SSH, restart, mutation, or secret
payload. Stable lexical tie-breaking produces the topological order.
Validation rejects cycles, duplicate action IDs, missing dependencies,
non-canonical dependency order, dependencies after their consumers, edge-list
mismatches, and an approval action placed before validation actions. A blocker
action prevents `READY_FOR_APPROVAL`.

## Risk and approval

Risk is deterministic and intentionally small:

- `LOW`: read-side package/evidence validation and audit preparation.
- `MEDIUM`: target ownership validation and the final approval checkpoint.
- `HIGH`: a recorded blocking condition requiring operator attention.
- `CRITICAL`: reserved for externally supplied or future contract extensions;
  validation prohibits approval readiness when present.

`READY_FOR_APPROVAL` means only that validated evidence may be presented to a
human decision-maker. It never means execution or production authorization.
The approval action itself is a non-executable intent.

## Blocking and security policy

Planning blocks for invalid schemas, package digest mismatch, dependency policy
other than `PASS`, non-ready/invalid/unavailable ingress, unavailable required
Mac inventory, non-Mac Control Plane ownership, a public edge other than Host
Caddy, Ubuntu ownership of Control Plane/CMS/Commerce, and any authorization
request. Closed schemas and recursive input screening reject unknown
security-sensitive fields, command payloads, secret-bearing fields, absolute
paths, and parent traversal. Error text does not reproduce rejected values.

Ingress `DEGRADED` is the one approval-visible warning supported by the
existing read-side status contract; it does not authorize execution.

## Boundaries and next step

DPL-03B adds no API route, apply service, executor, durable audit sink,
production evidence, or runtime/Ubuntu/network integration. The plan package
imports contracts and standard-library pure utilities only. DPL-03A classifies
it in `plan_services` while retaining all apply, worker, read, API, and legacy
quarantine protections.

DPL-03 is not complete. DPL-03C is the next step and must remain separately
scoped; any apply or authorization design requires an explicit future task and
must not interpret this plan as activation authority.
