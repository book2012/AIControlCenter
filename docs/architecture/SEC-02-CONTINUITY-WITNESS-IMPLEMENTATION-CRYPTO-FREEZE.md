# SEC-02 Continuity Witness Implementation and Crypto Architecture Freeze

Status: **FROZEN ARCHITECTURE ONLY; NOT IMPLEMENTED; NOT DEPLOYED**

```text
MILESTONE=SEC02_CONTINUITY_IDENTITY_LIFECYCLE_ARCHITECTURE_FROZEN
ARCHITECTURE_COMMIT=41e9f4f
DOCUMENTATION_RECONCILIATION_COMMIT=83cce29
CONTINUITY_WITNESS_ARCHITECTURE=FROZEN
FIRST_INSTALL_RESET_ATTACK_ARCHITECTURE_RESOLVED=YES
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO
IMPLEMENTATION_READY=NO
```

## 1. Decision and scope

This document freezes the implementation architecture choices for the external
Continuity Witness: Managed Device Attestation transport and freshness,
service boundary, durable record model, transaction model, signing primitives,
JSON API concepts, closed failure behavior, and audit evidence. It does not
implement, deploy, configure, validate, activate, or authorize any component.

The `DeviceInformation` transport architecture is selected, but its
implementation is not defined or implemented. This selection does not mean
that an MDM service is configured, DeviceInformation attestation has run, the
Witness or PostgreSQL is deployed, signing keys exist, a cloud host is
selected, or Production bootstrap is available. Consequently,
`CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO` remains an authoritative
operational-state fact.
`IMPLEMENTATION_READY=NO` also remains an authoritative operational-state fact.

This freeze does not change SEC-02 semantics, Governance core,
`ControlledExecutionPort`, or WU09. The Mac mini M4 remains the always-on Brain
and sole Control Plane. Ubuntu remains an optional stateless infrastructure
worker with zero authority and owns no AI workload, business logic,
application state, continuity state, or Control Plane authority.

## 2. Preserved continuity identity and lifecycle baseline

The frozen identity and lifecycle architecture remains authoritative:

```text
CONTINUITY_HOST_IDENTITY_DEFINED=YES
CONTINUITY_HOST_IDENTITY_OPERATOR_SELECTABLE=NO
CONTINUITY_HOST_IDENTITY_WITNESS_ASSIGNED=YES
CONTINUITY_HOST_IDENTITY_EVIDENCE_PRIMITIVE=APPLE_MANAGED_DEVICE_ATTESTATION
CONTINUITY_HARDWARE_BINDING=ATTESTED_UDID_AND_SERIAL_NUMBER
CONTINUITY_IDENTITY_USER_ENROLLMENT_ALLOWED=NO
CONTINUITY_GENESIS_ENROLLMENT_DEFINED=YES
CONTINUITY_RECOVERY_CEREMONY_DEFINED=YES
CONTINUITY_DECOMMISSION_DEFINED=YES
CONTINUITY_MIGRATION_DEFINED=YES
APPLE_SERVICES_ARE_CONTINUITY_WITNESS=NO
APPLE_ATTESTATION_ROLE=DEVICE_IDENTITY_AUTHENTICATION_EVIDENCE_ONLY
HUMAN_CONTINUITY_LIFECYCLE_APPROVER_DEFINED=YES
```

Continuity evidence remains a required precondition and never authorization.
Neither Apple, an MDM service, its transport, the Witness, nor a lifecycle
approval grants Production, install, bootstrap, SEC-02, execution, retry, or
rollback authority. The Witness lifecycle never invokes
`ControlledExecutionPort`, executes WU09, commands Ubuntu, installs a release,
or advances Production state.

## 3. Selected Managed Device Attestation transport

The selected transport is Apple MDM `DeviceInformation`. ACME is not selected
for Continuity Witness identity evidence.

```text
MDA_TRANSPORT_ARCHITECTURE_DEFINED=YES
CONTINUITY_WITNESS_MDA_TRANSPORT=DEVICE_INFORMATION
MDA_DEVICE_INFORMATION_SELECTED=YES
MDA_ACME_SELECTED_FOR_CONTINUITY_WITNESS=NO
MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO
MDA_TRANSPORT_IMPLEMENTED=NO
```

`DeviceInformation` is selected only to obtain device-identity authentication
evidence. The future MDM service and transport are evidence conduits, not a
Control Plane, continuity authority, lifecycle approver, or source of any
mutation authority. Caller input and MDM assertions cannot replace validation
of the Apple attestation certificate chain and required attested values.

## 4. Freshness, caching, and evaluation scope

An identity evaluation is the bounded device-identity authentication evaluation
used for a `GENESIS`, `RECOVERY`, `DECOMMISSION`, or `MIGRATION` lifecycle
decision. Every such evaluation receives a fresh, random, Witness-generated
32-byte nonce.

```text
MDA_DEVICE_ATTESTATION_NONCE_SIZE_BYTES=32
MDA_FRESHNESS_BINDING=DEVICE_ATTESTATION_NONCE_EQUALS_ATTESTED_FRESHNESS_CODE
```

For the current evaluation, the expected `DeviceAttestationNonce` must exactly
equal the freshness-code value validated from the attestation leaf certificate.
A mismatch is never tolerated or weakened for availability.

Apple `DeviceInformation` may return cached attestation evidence because new
attestation generation is rate-limited. Cached evidence whose freshness code
does not match the current evaluation nonce is not fresh evidence and is
classified `UNAVAILABLE` for that evaluation.

```text
DEVICE_INFORMATION_CACHED_ATTESTATION_MAY_AUTHORIZE_LIFECYCLE_MUTATION=NO
MDA_FRESHNESS_MISMATCH_FAILS_CLOSED=YES
MDA_UNAVAILABLE_EVIDENCE_IMPLIES_GENESIS=NO
MDA_RETRY_AUTHORITY_FROM_RATE_LIMIT=NO
```

No automatic retry authority is created by caching, rate limiting, timeout, or
unavailability. A future retry is a new identity evaluation with new evidence
and, for any requested lifecycle mutation, a new exact Human Continuity
Lifecycle Approval bound to that evaluation and operation.

An ordinary read-only lookup of Witness status or history does not require a
new Apple attestation. It remains read-only and grants zero authority. Every
lifecycle state mutation requires fresh current-evaluation MDA evidence.

## 5. Witness service boundary

The Continuity Witness is external to Mac application-accessible governed
state and owns durable continuity evidence state. It is not AIControlCenter and
is not a Control Plane. AIControlCenter consumes signed Witness evidence through
a purpose-specific adapter over a JSON HTTPS API.

The Witness cannot command the Mac or Ubuntu, invoke
`ControlledExecutionPort`, install releases, bootstrap SEC-02, or grant
Production mutation authority. The API exposes no shell, generic remote
command, arbitrary execution, generic infrastructure-control, or DPL execution
surface. DPL is never routed through `UbuntuWorkerClient.execute` or a generic
remote command, and Linux systemd Control Plane artifacts remain
`LEGACY_UNSUPPORTED`.

The public-edge and Witness-ingress facts are:

```text
AICONTROLCENTER_PUBLIC_EDGE=HOST_CADDY
CONTINUITY_WITNESS_INGRESS_TOPOLOGY_DEFINED=NO
CONTINUITY_WITNESS_CLOUD_HOST_SELECTED=NO
```

Host Caddy is the Mac AIControlCenter public edge only. External Continuity
Witness ingress, reverse proxy, TLS termination, DNS, network provider, cloud
host, MDM vendor, and deployment topology remain undefined. The external
Witness remains evidence authority only and never a second Control Plane. A
desired-state package is never activation authorization.

## 6. Durable relational record model

The selected durable-state model is a PostgreSQL-compatible transactional
relational architecture. PostgreSQL is the preferred replaceable open-source
infrastructure, not a selected or deployed Production service.

At minimum, the logical schema contains:

- `continuity_hosts`;
- `continuity_transitions`;
- `identity_evaluations`;
- `lifecycle_approval_claims`;
- `lifecycle_operations`;
- `witness_challenges`; and
- `audit_events`.

Each `continuity_hosts` record contains at least:

- a Witness-assigned immutable `continuity_host_id`;
- an immutable hardware-binding digest;
- enrollment generation;
- lifecycle state;
- highest `release_version`;
- highest `bootstrap_trust_source_version`;
- record generation;
- previous transition digest;
- created timestamp; and
- updated timestamp.

Hardware lookup derives a deterministic digest from the exact, successfully
validated attested UDID and serial-number values. Canonical field boundaries
and domain separation must prevent ambiguous concatenation. Raw or derived
caller-supplied host identifiers are not authoritative, and the caller cannot
select `continuity_host_id`.

Historical host, evaluation, transition, approval-claim, lifecycle-operation,
challenge, and audit records are never hard deleted by ordinary operation.
Retention, partitioning, backup, restore, and disaster-recovery implementations remain
future architecture and operational work and may not weaken this historical
continuity requirement.

## 7. Durable approval claim and transaction model

Human Continuity Lifecycle Approval uses these frozen states:

```text
AVAILABLE
DURABLY_CLAIMED
COMMITTED
FAILED_CONSUMED
UNCERTAIN_CONSUMED
```

```text
LIFECYCLE_APPROVAL_DURABLE_CLAIM_REQUIRED=YES
ROLLBACK_MAY_RESTORE_APPROVAL_AUTHORITY=NO
FAILED_CONSUMED_REUSABLE=NO
UNCERTAIN_CONSUMED_REUSABLE=NO
STRANDED_DURABLY_CLAIMED_REUSABLE=NO
DURABLY_CLAIMED_REUSABLE=NO
DURABLE_CLAIM_ITSELF_PERMANENTLY_CONSUMES_AUTHORITY=YES
TERMINALIZATION_WRITE_REQUIRED_TO_PREVENT_REUSE=NO
CLAIM_STEALING_ALLOWED=NO
AUTOMATIC_CLAIM_RECOVERY_ALLOWED=NO
AUTOMATIC_RETRY_AUTHORITY=NO
DATABASE_MUTATION_RESULT_ATOMIC=YES
HTTP_RESPONSE_DELIVERY_ATOMIC_WITH_DATABASE=NO
```

Stage A validates the exact lifecycle approval, binds the exact operation and
evaluation, and performs `AVAILABLE` -> `DURABLY_CLAIMED`. Once `DURABLY_CLAIMED`
exists, the approval is permanently non-reusable, regardless
of any later Stage B rollback, timeout, crash, disconnect, ambiguous
acknowledgement, reconciliation failure, or terminal-state update failure.

If the durable-claim outcome is ambiguous, processing fails closed. The
Witness does not execute lifecycle mutation, steal the claim, recreate
authority, or automatically recover the claim. A stranded `DURABLY_CLAIMED`
approval is non-reusable and permits read-only reconciliation only.

Stage B requires the exact `DURABLY_CLAIMED` approval, recollects and
revalidates all required preconditions, and may atomically transition
`DURABLY_CLAIMED` -> `COMMITTED` inside exactly one lifecycle mutation
transaction using serializable semantics or a proven stronger equivalent. That
same transaction persists the lifecycle state mutation, transition append,
digest advancement, required audit append, and durable lifecycle operation
result. If Stage B rolls back, approval state may remain `DURABLY_CLAIMED`, but
authority is not restored and the claim remains permanently non-reusable.

A definitive mutation failure may be durably classified `FAILED_CONSUMED`. An
uncertain outcome may be durably classified `UNCERTAIN_CONSUMED`. Neither
terminalization is required to make the approval non-reusable:
`DURABLY_CLAIMED` has already permanently consumed its authority. A later
mutation attempt requires a new evaluation and new exact lifecycle approval.

### 7.1 GENESIS

GENESIS requires fresh valid identity evidence, a GENESIS history lookup that
finds no historical binding for the validated hardware, and one exact
`GENESIS_ENROLLMENT` approval processed through Stages A and B. Stage B rechecks
historical absence, assigns a new `continuity_host_id`, creates the host record,
appends transition and audit evidence, advances the digest chain, persists the
operation result, and commits. A caller-selected host identity is prohibited.

### 7.2 RECOVERY

RECOVERY requires fresh valid identity evidence for the existing hardware and
one exact `RECOVERY` approval processed through Stages A and B. Stage B
preserves `continuity_host_id` and enrollment generation, cannot decrease
either version maximum, and atomically appends the recovery transition and
audit evidence, advances the digest chain, and persists the operation result.

### 7.3 DECOMMISSION

DECOMMISSION requires fresh valid identity evidence and one exact
`DECOMMISSION` approval processed through Stages A and B. Stage B atomically
appends the terminal transition and audit evidence, advances the digest chain,
and persists the operation result. Ordinary operation cannot recover, reenroll,
or hard-delete a decommissioned identity.

### 7.4 MIGRATION

MIGRATION requires the existing predecessor record, fresh valid successor
hardware evidence, and one exact `MIGRATION` approval processed through Stages
A and B. Stage B makes the predecessor `DECOMMISSIONED`, assigns the successor
a new `continuity_host_id`, records predecessor lineage, preserves nondecreasing
version maxima, appends all transitions and audit evidence, advances the digest
chain, and persists the operation result atomically. The predecessor identity
is never transferred to the successor.

This durable-claim model applies identically to GENESIS, RECOVERY,
DECOMMISSION, and MIGRATION. Any partial, ambiguous, timed-out, disconnected,
or otherwise uncertain outcome grants zero continuation, replay, completion,
or retry authority.

## 8. Cryptographic primitives and key separation

Ed25519 is selected for Witness response signatures and Human Continuity
Lifecycle Approval signatures.

```text
WITNESS_SIGNING_PRIMITIVE=ED25519
LIFECYCLE_APPROVAL_SIGNING_PRIMITIVE=ED25519
WITNESS_AND_LIFECYCLE_KEYS_SEPARATE=YES
```

The purpose-separated key identities are:

```text
CONTINUITY_WITNESS_SIGNING_KEY
CONTINUITY_LIFECYCLE_APPROVER_KEY
```

They are never the same key. Neither key may be a Release Authority key, Human
Bootstrap Approver key, SEC-02 issuer key, or Production execution
authorization key. Neither private key may live on Ubuntu. A caller cannot
provide, replace, select, or override a signing key.

Future custody must provide private-key non-export where supported by the
selected custody implementation and enforce least privilege. Rotation must
preserve verification of all historical signed evidence through durable,
purpose-bound key identity and validity metadata. Compromise requires a
separately frozen fail-closed recovery architecture; silent replacement,
automatic trust, historical signature reinterpretation, and rollback are
prohibited.

No cloud, HSM, key-management vendor, custody product, key provisioning
ceremony, rotation ceremony, or compromise-recovery implementation is selected.

```text
KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO
CLOUD_HOST_SELECTED=NO
```

## 9. Frozen JSON HTTPS API concepts

The purpose-specific API concepts are:

```text
POST /v1/identity-evaluations
GET /v1/identity-evaluations/{evaluation_id}
GET /v1/continuity-hosts/{continuity_host_id}
GET /v1/lifecycle-operations/{operation_id}
POST /v1/lifecycle/genesis
POST /v1/lifecycle/recovery
POST /v1/lifecycle/decommission
POST /v1/lifecycle/migration
```

Mutation endpoints never accept a caller-selected `continuity_host_id` for
GENESIS, retry flags, force flags, rollback flags, bypass flags, or reusable
approval authority. An approval is exact, operation-bound, evaluation-bound,
single-use, and must be durably claimed before lifecycle mutation.

The database transaction persists the lifecycle operation result and the
source facts required to produce or reproduce the signed Witness evidence
response. HTTP response transmission occurs only after commit and is not part
of the database transaction.

If final database COMMIT acknowledgement, connection state, or HTTP response delivery is
ambiguous, do not repeat the mutation POST, create retry authority, restore or
recreate approval authority, or steal or recover the claim. Perform read-only
exact-result reconciliation only through the lifecycle-operation lookup.

```text
AMBIGUOUS_COMMIT_ACK_MUTATION_RETRY_ALLOWED=NO
AMBIGUOUS_COMMIT_ACK_READ_ONLY_RECONCILIATION_ONLY=YES
EXACT_COMMITTED_OPERATION_REQUIRED_FOR_RECONCILED_SUCCESS=YES
```

Read-only reconciliation may report success only if the exact expected
`COMMITTED` operation exists and exactly matches the expected operation ID,
evaluation ID, operation type, approval claim, host and transition result, and
durable digest facts. Missing, conflicting, malformed, or uncertain evidence
fails closed; the approval remains permanently non-reusable whether represented
as `DURABLY_CLAIMED` or `UNCERTAIN_CONSUMED`. A later mutation attempt requires
a new evaluation and new exact approval. Exact `COMMITTED` evidence may be
reported as success, but grants no new mutation authority. Reconciliation
grants zero mutation, retry, rollback, install, bootstrap, SEC-02, execution,
release, or Production authority.

Every response is a signed Witness evidence envelope. An envelope binds its
schema and operation, request/evaluation identity, classification, relevant
record generation and transition digest, issued time, Witness key ID, and
response payload digest. A signed response is evidence only and grants no
install, bootstrap, SEC-02, execution, retry, rollback, or Production authority.
Vendor-specific networking, authentication products, service discovery, and
availability topology are not frozen here.

## 10. Closed classifications and failure behavior

The implementation boundary recognizes these closed result classes:

```text
VALID
GENESIS_ELIGIBLE
RECOVERY_REQUIRED
DECOMMISSIONED
UNAVAILABLE
MALFORMED
UNCERTAIN
```

`VALID` is the implementation-boundary representation of valid continuity
evidence; it does not add a new lifecycle state or alter the previously frozen
SEC-02 or continuity eligibility semantics. Only an explicitly eligible state
plus the required exact lifecycle approval may enter the corresponding
transactional mutation. No classification itself is authorization.

`UNAVAILABLE`, `MALFORMED`, and `UNCERTAIN` grant zero mutation authority.
Network timeout, Apple attestation failure, stale cached attestation,
certificate-chain failure, nonce mismatch, missing serial number, missing UDID,
database ambiguity, signature failure, transaction uncertainty, and audit-write
uncertainty all fail closed. Unavailable or unverifiable evidence never implies
GENESIS, and failure creates no automatic retry authority.

## 11. Immutable audit evidence

Every identity evaluation and lifecycle transition produces immutable,
append-only audit evidence containing at least:

- evaluation ID;
- operation;
- `continuity_host_id` when already established;
- hardware-binding digest;
- challenge digest, never reusable challenge or authority;
- MDA evidence digest;
- lifecycle approval digest and durable claim identity;
- lifecycle operation ID and durable result;
- previous transition digest;
- resulting transition digest;
- timestamps;
- Witness signing key ID; and
- final classification.

Required audit evidence is committed atomically with a lifecycle mutation.
Audit-write ambiguity makes the Stage B lifecycle mutation outcome uncertain
and fails closed. The approval is already permanently non-reusable because it
was `DURABLY_CLAIMED`. It may subsequently be represented as
`UNCERTAIN_CONSUMED` if that classification is durably established, but no
terminalization write can recreate, restore, or be required to destroy
authority. Audit evidence is evidence only; it is not an approval,
credential, capability, command, or authorization and grants zero authority.

## 12. Whole-document architecture consistency review

The selected DeviceInformation transport supplies only authenticated device
identity evidence and does not become the Witness or Control Plane. Exact nonce
binding makes cached mismatch fail closed without inventing retry authority.
Read-only history lookup remains separate from lifecycle evaluation, while each
lifecycle mutation requires fresh evidence and exact single-use human approval.

Witness-assigned identity, deterministic validated-hardware lookup, immutable
history, durable pre-mutation approval claims, serializable mutation
transactions, append-only transitions, audit evidence, durable operation
results, and signed response envelopes form one consistent fail-closed
boundary. Database-result atomicity is explicitly separate from post-commit
HTTP delivery, and ambiguity permits exact read-only reconciliation only.
GENESIS cannot be inferred from local or remote evidence
absence. RECOVERY preserves identity and maxima. DECOMMISSION is terminal.
MIGRATION assigns a new successor identity and atomically terminates the
predecessor without reducing maxima.

Ed25519 key purposes are separated from each other and from all release,
bootstrap, SEC-02, and execution authorities. Undefined key custody and cloud
hosting remain explicit blockers. None of these architecture selections makes
the Witness implemented, deployed, validated, Production-ready, or authorized
to mutate Production.

The review finds no change to SEC-02 semantics, Governance core,
`ControlledExecutionPort`, WU09, Mac Control Plane ownership, Ubuntu's
zero-authority status, or the existing separation of read, plan, and apply.

## 13. Preserved operational state

```text
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO
MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO
MDA_TRANSPORT_IMPLEMENTED=NO
KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO
CLOUD_HOST_SELECTED=NO
IMPLEMENTATION_READY=NO
SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY
BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
```

No Witness, relational database, MDM configuration, DeviceInformation
attestation, signing key, cloud hosting, Production bootstrap, or operational
validation is asserted to exist.

## 14. Final architecture-only gates

```text
SEC02_CONTINUITY_WITNESS_IMPLEMENTATION_CRYPTO_FREEZE_GATE=PASS_FROZEN_ARCHITECTURE_ONLY
MDA_TRANSPORT_SELECTION_GATE=PASS_DEVICE_INFORMATION_ARCHITECTURE_SELECTED_NOT_IMPLEMENTED
DEVICE_INFORMATION_CACHE_SAFETY_GATE=PASS_CACHED_MISMATCH_FAILS_CLOSED
CONTINUITY_WITNESS_CONTROL_PLANE_SEPARATION_GATE=PASS
CONTINUITY_WITNESS_TRANSACTION_MODEL_GATE=PASS_ATOMIC_FAIL_CLOSED
CONTINUITY_WITNESS_CRYPTO_PRIMITIVE_GATE=PASS_ED25519_PURPOSE_SEPARATED
KEY_CUSTODY_IMPLEMENTATION_GATE=BLOCKED_UNDEFINED
CLOUD_HOST_SELECTION_GATE=BLOCKED_UNDEFINED
IMPLEMENTATION_READY=NO
```

## 15. Change and activity attestation

```text
SEC02_SEMANTICS_CHANGED=false
GOVERNANCE_CORE_CHANGED=false
CONTROLLED_EXECUTION_PORT_CHANGED=false
WU09_FILES_CHANGED=false
CANONICAL_RERUN_REQUIRED=NO
PRODUCTION_ACCESS_PERFORMED=false
PRODUCTION_MUTATION_PERFORMED=false
PRODUCTION_AUTHORIZATION_CONSUMED=false
DOCKER_RUNTIME_ACCESSED=false
GIT_MUTATION=false
```

`GIT_MUTATION=false` means no staging, commit, push, reset, amend, branch
rewrite, or other Git-state mutation is authorized or performed. This requested
untracked architecture document is a working-tree filesystem addition only.
