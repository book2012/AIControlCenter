# SEC-02A7 Adapter Ports and Compatibility Mappings

Status: `SEC-02A7_ADAPTER_PORTS_AND_COMPATIBILITY_MAPPINGS_VALIDATED`

Next: `SEC-02A8 ORCHESTRATION POLICY AND SAFETY TESTS`

## Boundary

A7 defines Governance-owned Python protocols, the minimum immutable typed
persistence descriptors, and an immutable declarative compatibility catalog.
It adds no concrete operational adapter, orchestration, durable storage,
Production capability, public mutation API, retry, rollback, compensation, or
automatic replay. No A7 module accesses the filesystem, environment, secrets,
network, subprocess, SQLite, providers, Ubuntu, Runtime, or Production.

Dependencies point inward. Port modules import only A2-A5 Governance domain
types and standard-library typing or immutable-model facilities. Compatibility
mappings name existing operational boundaries as strings and never import
them.

## Port contracts

| Port | Typed boundary | Authority restriction |
|---|---|---|
| `PreconditionObservationPort` | authorization request to precondition snapshot | observation only; pure validators may be reused by a later adapter |
| `GitReadonlyEvidencePort` | authorization request to value-free `PreconditionBinding` | no checkout, reset, commit, push, or fetch |
| `RuntimeIdentityObservationPort` | authorization request to value-free `PreconditionBinding` | no activation, restart, or launchd mutation |
| `GovernanceAuditPort` | `GovernanceAuditEventRecord` to persistence receipt | persists Governance-decided facts; makes no policy decision |
| `EvidencePersistencePort` | A5 evidence bundle and manifest to persistence receipt | storage policy arrives in A9; persistence grants no authority |
| `ControlledExecutionPort` | A5 execution request to A5 execution receipt | one method call is one bounded invocation; uncertainty returns to Governance |
| `PostconditionValidationPort` | A5 execution receipt to A5 postcondition report | validates facts; cannot authorize retry or rollback |

There is no generic payload, environment, command, provider, or remote-execute
bag. The persistence descriptors are immutable, value-free acknowledgments and
do not contain behavior.

## Authority ownership

AIControlCenter Governance exclusively owns authorization lifecycle,
precondition-binding policy, mutation-budget policy, irreversible consumption,
retry and rollback prohibition, audit/evidence policy, and orchestration
policy. A desired state or compatibility mapping never grants authorization.

Adapters may collect observations, return typed read-only evidence, persist
typed audit/evidence, cross one already-governed bounded capability boundary,
validate postconditions, and return factual receipts. They cannot approve or
create authorization, make stale authority reusable, widen scope or budget,
decide retry or rollback, execute compensation, or own platform business
logic. `remaining_count` is never an adapter loop instruction.

## Declarative compatibility classifications

- Deployment preflight collection is `WRAP_AS_ADAPTER_LATER`; its pure
  validators remain reusable.
- `core/deployment/git_readonly_evidence/` is
  `REUSE_UNCHANGED_BEHIND_PORT`.
- `ops/macos/runtime/` is observation-only and
  `WRAP_AS_ADAPTER_LATER`.
- Deployment audit contracts, ports, writer, and recovery are reusable behind
  `GovernanceAuditPort`; Governance still decides audit policy.
- `core/governance/operations/` is `RETAIN_DOMAIN_SPECIFIC` as operational
  audit scheduling/read-model capability and is explicitly not authorization
  authority.
- `core/deployment/operational_bootstrap_execution/` is
  `WRAP_AS_ADAPTER_LATER` behind the controlled execution port.
- `core/deployment/bootstrap_evidence_recovery/` is
  `REFACTOR_BEFORE_INTEGRATION`: chain/recovery concepts are reusable, but its
  historical `/private/tmp` assumption is unsuitable for authoritative durable
  Governance evidence.
- Shopping deployment authorization/idempotency stays
  `RETAIN_DOMAIN_SPECIFIC`. Governance supplies generic authorization,
  consumption, budget, audit, and evidence; Shopping retains eligibility and
  business-write semantics.

Every A7 mapping has `concrete_adapter_present=false`.

## Ubuntu and Shopping boundaries

Ubuntu remains an optional stateless infrastructure Worker. A future adapter
may expose only bounded stateless infrastructure operations through JSON
interfaces. Ubuntu owns no AI workload, Governance authority, authorization
decision, business logic, application state, or Control Plane state. A7 adds no
Ubuntu adapter.

Shopping business rules remain in the AIControlCenter Shopping domain, while
WooCommerce remains the Commerce Engine. Governance does not absorb product
eligibility, pricing rules, recommendation logic, customer logic, or order
business policy. A7 adds no WooCommerce write adapter.

## Validation state

Three focused test modules specify protocol shape, typed boundaries,
deterministic/duplicate-safe mappings, authority ownership, and AST-enforced
side-effect exclusions. Initial external validation reported `1 failed, 193
passed in 1.56s`. R1 classified the failure as
`PROTOCOL_RUNTIME_INIT_TEST_INSPECTION_DEFECT` and fixed the Protocol-only
interface gate. The diagnosis identified test-inspection semantics, not
implementation `__init__` semantics: the gate must inspect whether the
Protocol class body explicitly declares `__init__`, without treating inherited
runtime Protocol initialization behavior as an implementation constructor.

The final focused Governance regression reported `194 passed in 1.53s`,
validating `SEC-02A7_ADAPTER_PORTS_AND_COMPATIBILITY_MAPPINGS_VALIDATED`. This
was not a full repository regression. A7 contains abstract Governance ports
only and no concrete Production adapter. Adapters cannot authorize, widen
scope or mutation budget, or decide retry or rollback. Git evidence remains
read-only; Runtime identity remains observation-only; Governance Operations
remains operational audit/read-model only; Shopping business rules remain
Shopping-owned; and Ubuntu remains a stateless Worker with zero Governance
authority. No
`SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY` claim is made. Notion
remains `DEFERRED_UNTIL_FINAL_PHASE`.
