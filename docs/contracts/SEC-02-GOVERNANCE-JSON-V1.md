# SEC-02 Governance JSON v1 Contract Catalog

Status: `SEC-02A6_JSON_SCHEMA_REGISTRY_AND_CONTRACT_TESTS_VALIDATED`

The frozen v1 family is now implemented as 16 JSON Schema Draft 2020-12
resources under
`core/governance/control_plane/contracts/schemas/v1/*.json`. The deterministic
local-only registry is
`core/governance/control_plane/contracts/registry.py`. Valid and invalid
fixtures plus registry, schema, and fixture contract tests live under
`tests/governance/control_plane/`. A1 semantic names remain frozen. Schemas are
machine enforcement, not authorization authority, and add no Production
capability.

This is the canonical v1 semantic catalog. It freezes names, ownership,
lifecycle roles, major field families, and invariants. The implemented schemas
encode those frozen contracts without changing their semantics or granting
authorization.

## Family-wide rules

All contracts are canonical-JSON compatible, explicitly schema-versioned,
deterministic where produced by the domain, and reject unsafe data. Immutable
identities, digests, scope, target, action/budget, snapshot, and lifecycle
references cannot be changed after their owning record is issued. Exact
bindings—not field presence alone—are authoritative.

Forbidden in every contract: provider secret values; secret-derived hashes,
comparisons, prefixes, or suffixes; credential identifiers where avoidable;
authorization material granting access; raw Authorization headers; cookies;
raw environment dumps; secret-bearing commands; and opaque provider responses
that may contain credentials. These data must not be read to build governance
identity.

## Contract catalog

### 1. `GovernanceAuthorizationRequest`

- Purpose: request an explicitly scoped governance lifecycle; it grants no
  mutation authority.
- Owner: governance domain.
- Lifecycle role: creates `REQUESTED`.
- Major fields: schema/lifecycle/request identity, requester, operation type,
  target, environment, reason, requested scope, requested mutation-budget line
  items, manifest/package/plan digests, requested time.
- Immutable bindings: lifecycle/request identity, requester, target,
  environment, scope, action types/counts, and supplied artifact digests.
- Forbidden data: all family-wide categories, especially access tokens or
  secret-bearing operation arguments.
- Existing relationship: references deployment plans/manifests and shopping
  intents without taking ownership of their business semantics.

### 2. `GovernancePreconditionSnapshot`

- Purpose: bind authorization-relevant observations into one exact snapshot.
- Owner: governance domain; observations arrive through application ports.
- Lifecycle role: collected before decision and recollected before consumption.
- Major fields: schema/snapshot identity, collection time, collector identities,
  target identity, Git state, runtime identity, security-state classes,
  manifest bindings, operational observations, policy version, snapshot digest.
- Immutable bindings: all observations, collector identities, policy version,
  and digest.
- Forbidden data: raw filesystem/process/environment/command output and all
  family-wide categories.
- Existing relationship: wraps read-only Git evidence, runtime identity,
  deployment preflight, and value-free security metadata.

### 3. `GovernanceAuthorizationDecision`

- Purpose: record an explicit human approve/reject decision.
- Owner: governance domain.
- Lifecycle role: supports `REQUESTED -> AUTHORIZED` or `REQUESTED -> REJECTED`.
- Major fields: schema/decision identity, request identity, approver identity,
  decision, reason codes, decision time, expiry, approved scope, approved budget,
  bound precondition snapshot digest.
- Immutable bindings: request, approver, decision, scope, budget, snapshot, and
  validity window.
- Forbidden data: signatures/tokens that independently grant system access and
  all family-wide categories.
- Existing relationship: preserves deployment approval and separation-of-duty
  rules behind governance semantics.

### 4. `GovernanceAuthorizationReceipt`

- Purpose: represent issued, exact-bound governance authority.
- Owner: governance domain.
- Lifecycle role: materializes `AUTHORIZED`; it is not execution itself.
- Major fields: schema/authorization identity, request/decision identities,
  state, exact bindings, issue/expiry times, use constraint, mutation-budget
  identity, receipt digest.
- Immutable bindings: every identity, target/scope/snapshot/budget binding,
  validity window, and receipt digest.
- Forbidden data: bearer credentials or replayable external authorization
  material and all family-wide categories.
- Existing relationship: generalizes deployment operational permits while
  leaving DPL policy in `core/deployment/*`.

### 5. `GovernanceAuthorizationStateRecord`

- Purpose: durably record one legal authorization transition.
- Owner: governance domain; persisted through a governance port.
- Lifecycle role: transition/audit record for the exact five-state machine.
- Major fields: schema/record and authorization identities, previous/current
  state, transition reason, transition time, precondition comparison digest,
  audit-event identity.
- Immutable bindings: authorization identity, state pair, reason, comparison,
  and audit link.
- Forbidden data: mutable state patches and all family-wide categories.
- Existing relationship: maps to append-only audit/replay storage without
  adopting deployment-specific state names.

### 6. `GovernanceMutationBudget`

- Purpose: bind authorized typed invocation limits and actual accounting.
- Owner: governance domain.
- Lifecycle role: authorized with the receipt and accounted across consumption
  and execution.
- Major fields: schema/budget and authorization identities; action line items
  containing `action_type`, `allowed_count`, `actual_invocation_count`,
  `completed_count`, `uncertain_count`, and `status`; consumption point.
- Immutable bindings: authorization, line-item action types, allowed counts, and
  workflow scope; accounting evolves only through valid domain events.
- Forbidden data: commands, arbitrary transport payloads, and family-wide data.
- Existing relationship: unifies counters around deployment and shopping typed
  writes without changing their action semantics.

Statuses are exactly `AVAILABLE`, `CONSUMED`, `EXHAUSTED`, and `VIOLATED`.
`remaining_count` is derived accounting only and never retry permission.

### 7. `GovernanceAuthorizationConsumptionReceipt`

- Purpose: prove atomic, irreversible authorization claim.
- Owner: governance domain; durable claim is supplied by a replay-state adapter.
- Lifecycle role: records `AUTHORIZED -> CONSUMED` before adapter invocation.
- Major fields: schema/claim identity, authorization/budget/execution-request
  identities, consumed time, replay-store sequence/hash, transaction status.
- Immutable bindings: claim, authorization, budget, execution request, and
  durable replay position.
- Forbidden data: reusable permit material, database connection data, and all
  family-wide categories.
- Existing relationship: wraps atomic permit claim and SQLite replay primitives.

### 8. `GovernanceExecutionRequest`

- Purpose: request one exact bounded typed adapter capability.
- Owner: governance application using domain-validated inputs.
- Lifecycle role: fixed before claim and invoked only after consumption/start
  evidence.
- Major fields: schema/execution-request identity, authorization/claim/budget
  identities, adapter capability, target, plan digest, requested time.
- Immutable bindings: all identities, typed capability, target, and plan digest.
- Forbidden data: generic shell/remote commands, secret-bearing arguments, and
  all family-wide categories.
- Existing relationship: delegates to deployment/shopping bounded ports; never
  to generic Ubuntu execution.

### 9. `GovernanceExecutionReceipt`

- Purpose: account for the exact adapter boundary and its result.
- Owner: bounded adapter, normalized by governance application/domain rules.
- Lifecycle role: execution outcome after authorization consumption.
- Major fields: schema/receipt and request identities, adapter identity, status,
  invocation/completed/uncertain counts, start/completion times, result digest,
  findings.
- Immutable bindings: request, adapter/capability identity, target, counts,
  result reference, and chronology.
- Forbidden data: raw provider responses, stdout/stderr, commands, environments,
  and all family-wide categories.
- Existing relationship: normalizes mature deployment and shopping receipts.

### 10. `GovernancePostconditionReport`

- Purpose: compare expected and observed state after execution.
- Owner: governance domain from observations supplied through validation ports.
- Lifecycle role: post-execution validation; never restores authorization.
- Major fields: schema/report identity, execution-receipt identity, validator
  identity, expected/observed state references, decision, reason codes, digest.
- Immutable bindings: execution receipt, validator, observations, decision, and
  digest.
- Forbidden data: raw host/provider output and all family-wide categories.
- Existing relationship: wraps deployment-specific postcondition validators.

### 11. `GovernanceFailureEvidence`

- Purpose: preserve fail-closed classification and accounting for any phase.
- Owner: governance domain.
- Lifecycle role: accompanies stopped, stale, rejected, uncertain, persistence,
  or violated outcomes.
- Major fields: schema/failure and lifecycle identities, phase, failure class,
  reason codes, authorization state, claim status, mutation accounting,
  retry-prohibited flag, rollback-prohibited flag, manual-action requirement.
- Immutable bindings: lifecycle/authorization/claim context, phase, reason,
  counts, and safety decisions.
- Forbidden data: exception dumps or raw responses that could leak family-wide
  categories.
- Existing relationship: generalizes DPL failure evidence and mandatory
  no-silent-recovery policy.

### 12. `GovernanceEvidenceManifest`

- Purpose: index and integrity-bind durable governance artifacts.
- Owner: governance domain; persisted by durable evidence adapter.
- Lifecycle role: durable evidence inventory and integrity root.
- Major fields: schema/manifest and lifecycle identities, ordered artifact
  entries, artifact types, digests, sizes, creation times, storage identity,
  manifest digest.
- Immutable bindings: ordering, artifact identity/type/digest/size, storage
  identity, and manifest digest.
- Forbidden data: artifact contents, sensitive absolute paths, storage
  credentials, and all family-wide categories.
- Existing relationship: reuses manifest/digest conventions; `/private/tmp`
  cannot be authoritative storage.

### 13. `GovernanceEvidenceBundle`

- Purpose: canonical lifecycle evidence envelope.
- Owner: governance domain.
- Lifecycle role: binds authorization, execution, validation, failure, audit,
  and closeout evidence.
- Major fields: schema/bundle identity, lifecycle references, authorization,
  preconditions, budget, claim, execution, postconditions, failure, audit,
  Git/documentation gate, bundle digest.
- Immutable bindings: all referenced identities/digests and bundle digest.
- Forbidden data: embedded unsafe/raw operational artifacts and all family-wide
  categories.
- Existing relationship: unifies existing DPL/SEC-01 evidence concepts through
  references and adapters, not replacement.

### 14. `GovernanceAuditEvent`

- Purpose: append one value-free lifecycle fact to durable audit history.
- Owner: governance domain; persisted by audit adapter.
- Lifecycle role: records decisions, transitions, claims, starts, receipts,
  validation, failures, and evidence closeout.
- Major fields: schema/event identity, sequence, event type, lifecycle identity,
  actor, authorization identity, evidence digests, previous hash, event hash,
  timestamp.
- Immutable bindings: sequence, event/lifecycle/actor identities, evidence
  references, and hash chain.
- Forbidden data: mutable projections, raw operational payloads, and all
  family-wide categories.
- Existing relationship: reuses append-only deployment audit SQLite and
  governance operations projections without conflating observation with
  authorization.

### 15. `GovernanceGitDocumentationGateReport`

- Purpose: report repository/documentation closeout conditions when applicable.
- Owner: governance application from read-only Git/document checks.
- Lifecycle role: final closeout gate after durable evidence.
- Major fields: schema/report identity, branch, commit, worktree-clean state,
  upstream relation, required-document status, evidence-manifest digest,
  decision, reason codes.
- Immutable bindings: repository identity observations, document result,
  evidence manifest, and decision.
- Forbidden data: Git credentials, remote tokens, host-sensitive paths, and all
  family-wide categories.
- Existing relationship: wraps read-only Git evidence; the report cannot grant
  authorization.

### 16. `GovernanceApiEnvelope`

- Purpose: stable read/projection envelope for governance API consumers.
- Owner: governance presentation contract; source data remains domain-owned.
- Lifecycle role: exposes immutable projections and evidence references only.
- Major fields: schema version, generation time, status, data, error envelope,
  evidence references.
- Immutable bindings: schema/status semantics and evidence references for a
  generated response.
- Forbidden data: storage handles, mutable domain objects, raw errors, and all
  family-wide categories.
- Existing relationship: follows existing read-only governance API/dashboard
  projection patterns; it creates no mutation endpoint or authority.

## Lifecycle invariants

Authorization states and transitions are exactly those in the canonical
architecture. Revalidation precedes atomic consumption. Drift and expiry before
claim produce terminal `STALE`; post-claim failure remains `CONSUMED`. An
ambiguous claim fails closed. No contract, manifest, idempotency key, desired
state, or count grants authority by itself. There is no automatic retry or
rollback after the consumption boundary.

Execution order is fixed by the architecture: validate request; validate
authorization; recollect and compare preconditions; validate budget; consume;
persist start evidence; invoke exactly the typed adapter; receipt;
postconditions; durable evidence; applicable Git/document closeout.

## Compatibility boundary

v1 adapters may map existing deployment authorization, permit/replay, Git
evidence, runtime identity, audit SQLite, execution receipt, and evidence
capabilities without losing immutable bindings. Deployment retains deployment
policy; governance operations retains observation/scheduling/read models;
shopping retains eligibility and commerce-write semantics. Compatibility must
not weaken repository controls, create generic commands, or place authority on
Ubuntu.

## Versioning policy

Contract names above form the v1 family. Implementations must select an explicit
supported version and fail closed on unknown versions. Compatible additive
changes may occur only where a future schema explicitly allows them and they do
not change frozen semantics. Renaming fields, weakening required bindings,
changing state transitions/status meanings, broadening forbidden data, or
altering consumption/retry rules requires a new major contract family and an
explicit migration. Canonicalization and digest rules must remain deterministic
within a version.

All 16 Draft 2020-12 schemas, their exact registry bindings, and deterministic
valid/invalid fixture contracts are validated by the successful focused
governance regression: `173 passed in 1.39s`. The prior R1 blocker is classified
as `SEC-02A6-R1_CONTROLLER_REGISTRY_API_ASSUMPTION_DEFECT`: the controller
incorrectly assumed a public `registry.contract_names()` function, although the
frozen contract required behavior rather than that exact API name. It was not
an A6 contract implementation defect. No Production, provider, or Ubuntu
mutation and no execution adapter were involved. This result is not a full
repository regression. Next:
`SEC-02A7 ADAPTER PORTS AND COMPATIBILITY MAPPINGS`. Notion remains
`DEFERRED_UNTIL_FINAL_PHASE`. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made.
