# SEC-02 Governance Control Plane Architecture

Status: `SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`

Next: `SEC-02A9 DURABLE EVIDENCE AND API PROJECTION`

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
- `core/shopping/*` retains shopping eligibility and commerce-write semantics.
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

`STALE`, `CONSUMED`, and `REJECTED` are terminal.

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

After step 6, any failure means `STOP`: no automatic retry and no automatic
rollback. Authorization remains `CONSUMED`.

## Durable evidence

Authoritative operational evidence lives in configured durable Mac Control
Plane storage, never `/private/tmp`. It is canonical JSON, schema-versioned,
atomically written with restrictive permissions and durability confirmation,
and compatible with evidence manifests. Credential-related evidence is
value-free.

Git-tracked evidence is summary/closeout evidence only. It cannot grant
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
They must not decide authorization, widen scope, increase budget, decide retry
or rollback safety, silently replay authorization, own platform-wide policy, or
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

## Milestones

- A0: governance inventory — complete.
- A1: governance domain and JSON contract freeze — current, frozen by this
  document and the v1 catalog.
- A2: authorization domain models — next.
- A3: precondition snapshots and comparison.
- A4: mutation budgets and consumption semantics.
- A5: receipts, failures, and evidence domain.
- A6: v1 schema implementation and registry.
- A7: adapter ports and compatibility mappings — validated by the focused
  Governance regression, `194 passed in 1.53s`.
- A8: pure orchestration policy and safety tests — validated by the focused
  Governance regression, `231 passed in 1.42s`; milestone
  `SEC-02A8_ORCHESTRATION_POLICY_AND_SAFETY_TESTS_VALIDATED`. This was not a
  full repository regression.
- A9: durable evidence and API projection — next.
- A10: API/read-model and architecture closure preparation.

No milestone here authorizes Production activation. The architecture-ready
milestone is reserved for a later SEC-02A closure review and is not claimed.
