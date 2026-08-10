# SEC-02 Governance Control Plane Architecture

Status: `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`

Next: `SHOP-01A_SHOPPING_PLATFORM_ARCHITECTURE_AND_READ_ONLY_FOUNDATION`

This document is the canonical SEC-02 architecture freeze. SEC-02A is **not a
Production mutation implementation**. It establishes reusable Control Plane
governance contracts only. A desired state, manifest, idempotency key, or
available budget never grants authorization.

## Control Plane ownership

The Mac mini M4 is the always-on Brain. AIControlCenter is the single Control
Plane and owns governance, policy, orchestration, approval, authorization,
audit, deployment control, and business logic. Host Caddy remains the only
public edge. WordPress remains the CMS Engine and WooCommerce the Commerce
Engine.

Ubuntu is an optional stateless infrastructure Worker reached only through
bounded JSON APIs. It owns no AI workload, business logic, application state,
authorization, audit authority, replay state, or governance state. SEC-02 must
not create a generic remote-command path or route DPL through
`UbuntuWorkerClient.execute`.

Read-only-first, JSON-first, and Git-first are mandatory. Production mutation
always requires a separate, explicit human authorization.

## Bounded capability

The frozen boundary is:

```text
core/governance/control_plane/
    domain/
    application/
    ports/
    adapters/
    contracts/
```

- `domain/` is pure, immutable, deterministic, and JSON serializable. It has no
  filesystem, subprocess, network, SQLite, provider, Git-command, or clock
  access.
- `application/` is pure, immutable orchestration policy. It inspects domain
  facts and returns permission-only dispositions without invoking ports or
  adapters.
- `ports/` owns abstract typed boundaries. A7 adds no orchestration or external
  implementation; orchestration policy is deferred to A8.
- `adapters/` wrap existing capabilities and execute bounded typed operations.
- `contracts/` owns the SEC-02 registry and versioned governance JSON Schema
  family. Actual schemas are deferred.

Dependencies point inward: contracts and immutable domain semantics do not
depend on application orchestration or adapters; application code depends on
domain types and declared ports; adapters implement those ports. External
systems never call inward as policy owners.

## Preserved capability ownership

- `core/deployment/*` retains deployment business rules and mature DPL controls.
  SEC-02 wraps appropriate capabilities through ports; it does not replace them.
- `core/governance/operations/*` remains operational observation, audit
  scheduling, and read-model capability. It is not Production mutation
  authorization.
- AIControlCenter retains Shopping eligibility and all platform business logic;
  WordPress is the CMS Engine and WooCommerce is the Commerce Engine, not an
  owner of platform business logic.
- Existing audit SQLite, permit replay, Git evidence, runtime identity,
  deployment authorization, and evidence capabilities are reused behind
  governance ports where appropriate.

## Authorization lifecycle

The states are exactly `REQUESTED`, `AUTHORIZED`, `STALE`, `CONSUMED`, and
`REJECTED`.

```text
REQUESTED -> AUTHORIZED
REQUESTED -> REJECTED
AUTHORIZED -> STALE
AUTHORIZED -> CONSUMED
```

`STALE`, `CONSUMED`, and `REJECTED` are non-reusable terminal states.

- `REQUESTED` has no mutation authority.
- `AUTHORIZED` requires an explicit human decision bound to exact
  preconditions.
- Revalidation occurs before consumption. Bound drift produces `STALE`.
- Expiry before consumption produces `STALE` with
  `AUTHORIZATION_EXPIRED`.
- `REJECTED` means authority was never granted.
- `CONSUMED` is atomic, irreversible, and never reusable.
- Failure after consumption never restores authorization.
- Ambiguous claim or persistence state fails closed and remains non-reusable
  until manual inspection.
- Every attempt after `STALE`, `CONSUMED`, or `REJECTED` requires a new request,
  snapshot, and authorization lifecycle.

## Mutation budget

Each authorization contains one or more explicit action line items. Each line
item owns `action_type`, `allowed_count`, `actual_invocation_count`,
`completed_count`, `uncertain_count`, and `status`.

- `AVAILABLE`: authorization is not consumed and no controlled invocation has
  been crossed.
- `CONSUMED`: authorization has been claimed; zero or more authorized invocation
  boundaries may have been crossed and a line item may remain below its allowed
  count. It never implies retry permission.
- `EXHAUSTED`: the authorized invocation count is fully used for the line item
  or workflow.
- `VIOLATED`: an invariant or authorized count was exceeded or cannot be proven
  safe. This is a terminal safety incident and never triggers compensation.

`remaining_count` is accounting only. It is never permission to retry after a
controlled mutation failure. Authorization consumption and invocation
accounting are distinct: a claim can consume authorization before any adapter
boundary is crossed, while numeric invocation count changes only when that
boundary is crossed.

## Frozen execution order

1. Validate request/schema.
2. Validate authorization identity/scope.
3. Recollect bound preconditions.
4. Compare exact bindings/snapshot digest.
5. Validate action against mutation budget.
6. Atomically consume authorization.
7. Persist execution-start audit evidence.
8. Cross exactly the authorized adapter invocation boundary.
9. Record execution receipt.
10. Validate postconditions.
11. Persist durable evidence.
12. Close out the Git/documentation gate when applicable.

After step 6, `FAILED`, `UNCERTAIN`, `DRIFT`, failed postcondition, or failure
evidence means `STOP`: **NO AUTOMATIC RETRY** and **NO AUTOMATIC ROLLBACK**.
Authorization remains `CONSUMED`.

## Durable evidence

Authoritative operational evidence lives in configured durable Mac Control
Plane storage, never `/private/tmp`. It is canonical JSON, schema-versioned,
atomically written with restrictive permissions and durability confirmation,
and compatible with evidence manifests. Credential-related evidence is
value-free.

Git-tracked repository evidence JSON is canonical documentation/audit evidence,
not mutable application runtime state. It cannot grant
authorization, must exclude secret values and credential identifiers, and
should avoid host-sensitive absolute paths.

Governance evidence forbids provider secret values, secret-derived hashes or
comparisons, secret prefixes or suffixes, credential identifiers where
avoidable, access-granting authorization material, raw Authorization headers,
cookies, raw environment dumps, secret-bearing commands, and opaque provider
responses that may contain credentials. Secret values must not be read,
printed, hashed, compared, serialized, or used as governance identity.

## Adapter boundary

Adapters may collect observations, execute one bounded typed capability,
persist governance state, return typed receipts, and expose integrity or health.
They must not authorize, widen scope or budget, retry, roll back, silently
replay authorization, own platform-wide policy, or
expose raw secret-bearing process/environment data.

Ubuntu adapters are limited to stateless bounded JSON infrastructure calls.
They cannot own governance, replay, audit authority, or business logic and
cannot become generic remote command adapters.

## Test architecture

1. Pure unit tests cover deterministic domain rules.
2. Contract tests cover registry, compatibility, canonicalization, and fixtures.
3. Adapter tests cover typed boundary behavior and safety.
4. Isolated operational tests use local temporary roots and fake services.
5. Production validation is separately authorized.

SEC-02A does not execute layer 5.

## Non-goals

SEC-02A1 adds no source implementation, schemas, API mutation endpoints,
database migration, operational execution, provider access, Production access,
Ubuntu integration, retry, rollback, or generic command authority. It does not
move deployment or shopping business semantics into governance.

## A7 port and compatibility freeze

A7 defines read-only precondition, Git-evidence, and Runtime-identity
observation protocols; typed audit and evidence persistence protocols; a
single-invocation controlled execution protocol; and a read-only postcondition
validation protocol. Compatibility metadata is immutable and declarative. It
names operational boundaries without importing them, and every mapped concrete
adapter is absent.

External validation initially reported `1 failed, 193 passed in 1.56s`. R1
classified the failure as
`PROTOCOL_RUNTIME_INIT_TEST_INSPECTION_DEFECT` and fixed the Protocol-only
interface gate. The defect was in test-inspection semantics: the gate needed to
inspect whether a Protocol class body explicitly declared `__init__`; it did
not identify implementation `__init__` semantics. The final focused Governance
regression reported `194 passed in 1.53s`. This was not a full repository
regression.

Governance retains authorization, binding, mutation-budget, consumption,
retry/rollback prohibition, audit/evidence, and orchestration authority.
Ubuntu remains a stateless bounded-JSON infrastructure Worker with no
Governance authority. Shopping retains eligibility and commerce business-write
semantics; WooCommerce remains the Commerce Engine. See
`docs/architecture/SEC-02A7-ADAPTER-PORTS.md`.

## A8 orchestration safety freeze

A8 adds a pure application policy with exactly five dispositions:
`ALLOW_AUTHORIZATION_CONSUMPTION`, `ALLOW_SINGLE_INVOCATION`,
`REQUIRE_POSTCONDITION_VALIDATION`, `ALLOW_CLOSEOUT`, and `STOP`. All decisions
prohibit automatic retry and rollback. Failure evidence, invalid bindings,
non-authoritative lifecycle states, absent or drifted current preconditions,
missing consumption evidence, budget violations or exhaustion, failed or
uncertain execution, and failed postconditions take priority over progress.

The policy performs no consumption or invocation: authorization consumption is
a distinct gate, followed by a fresh current-precondition `MATCH` requirement
before one bounded invocation may be permitted. One policy permission maps to
one bounded invocation. Consumed authorization remains consumed after later
drift. Remaining mutation count is accounting only, never retry authority.
`FAILED`, `UNCERTAIN`, postcondition `FAIL`, and existing failure evidence each
produce `STOP`. There is no automatic retry, automatic rollback, or
compensation authority; postcondition `PASS` permits closeout only.

External validation of the focused Governance regression reported `231 passed
in 1.42s`, reaching
`SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. This was not a full
repository regression. See
`docs/architecture/SEC-02A8-ORCHESTRATION-SAFETY.md`.

## A9 durable evidence and API projection freeze

A9 adds a pure immutable storage policy over caller-supplied classification
facts and a typed, read-only Governance projection. Durable runtime evidence
belongs in an operator-configured external Control Plane data root, never the
repository working tree, immutable application source, or `/private/tmp`.
Historical controller reports under `/private/tmp` remain transient only.
Git-tracked evidence JSON is canonical documentation/audit evidence, not
mutable runtime state. Application code hard-codes no user-specific data root.

Acceptance requires atomic publication, restrictive permissions, durable
synchronization, manifest binding, caller-supplied non-secret identities and
digests, and value-free evidence. The deterministic API projection uses the
caller-supplied projection time and the unchanged A6 `GovernanceApiEnvelope`.
It grants or consumes no authorization and exposes no mutation, execution,
retry, rollback, or HTTP route. A9 adds no concrete persistence adapter.
Shopping business logic remains Shopping-owned; Ubuntu remains a stateless
Worker with no Governance authority. See
`docs/architecture/SEC-02A9-DURABLE-EVIDENCE-API-PROJECTION.md`.

External validation of the focused Governance regression reported `265 passed
in 1.45s`, reaching
`SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`. This was not a full
repository regression. `GovernanceApiEnvelope` compatibility and the
deterministic, read-only projection boundary were validated. A10 subsequently
performed the architecture closure review.

## A10 architecture closure

The A0-A10 architecture phase is complete, the A1-A9 canonical evidence chain
is `VALIDATED`, and the reusable architecture milestone is
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`. The supplied canonical
full repository regression passed exactly as:

```text
========= 2667 passed, 5 deselected, 437 warnings in 166.69s (0:02:46) =========
```

The prior focused Governance regression was `265 passed in 1.45s`. No test was
rerun for documentation closure.

## Milestones

- A0: governance inventory — complete.
- A1: governance domain and JSON contract freeze — complete.
- A2: authorization domain models — complete.
- A3: precondition snapshots and comparison — complete.
- A4: mutation budgets and consumption semantics — complete.
- A5: receipts, failures, and evidence domain — complete.
- A6: v1 schema implementation and registry — complete.
- A7: adapter ports and compatibility mappings — validated by the focused
  Governance regression, `194 passed in 1.53s`.
- A8: pure orchestration policy and safety tests — validated by the focused
  Governance regression, `231 passed in 1.42s`; milestone
  `SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. This was not a
  full repository regression.
- A9: pure durable-evidence policy and read-only API projection — validated by
  the focused Governance regression, `265 passed in 1.45s`; milestone
  `SEC-02A9_DURABLE_EVIDENCE_AND_API_PROJECTION_VALIDATED`. This was not a full
  repository regression.
- A10: architecture closure review — complete; milestone
  `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`.

No milestone here authorizes Production activation. The architecture-ready
milestone confirms reusable architecture only. No concrete Production mutation
adapter was implemented by SEC-02A. Git closeout will be performed by the
external controller. Notion actual external synchronization has not been
performed; documentation payload status is `READY_FOR_FINAL_SYNC`. See
`docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md`.
