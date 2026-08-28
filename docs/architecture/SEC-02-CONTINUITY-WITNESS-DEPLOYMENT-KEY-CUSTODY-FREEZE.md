# SEC-02 Continuity Witness Deployment and Key Custody Architecture Freeze

Status: **FROZEN ARCHITECTURE ONLY; NOT IMPLEMENTED; NOT DEPLOYED**

## 1. Decision and scope

This document freezes the deployment and key-custody architecture for the
external Continuity Witness. It selects AWS as the cloud provider and freezes
logical service, datastore, immutable-history, privacy-index, signing-key,
human-approval-key, serialization, and failure boundaries without provisioning,
configuring, deploying, activating, or operationally validating any resource.

This freeze preserves the committed identity/lifecycle and implementation/crypto
architectures without changing SEC-02 semantics, Governance core,
`ControlledExecutionPort`, or WU09. Architecture selection is not implementation
authority, desired state is not activation authorization, and no component in
this document grants Production mutation authority.

```text
SEC02_CONTINUITY_WITNESS_DEPLOYMENT_KEY_CUSTODY_ARCHITECTURE_FROZEN=YES
FIRST_INSTALL_RESET_ATTACK_ARCHITECTURE_RESOLVED=YES
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
CONTINUITY_WITNESS_DEPLOYMENT_ARCHITECTURE_DEFINED=YES
KEY_CUSTODY_ARCHITECTURE_DEFINED=YES
CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO
KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO
IMPLEMENTATION_READY=NO
```

## 2. Preserved authority boundaries

The Mac mini M4 remains the always-on Brain and sole Control Plane.
AIControlCenter alone owns governance, policy, orchestration, approval,
authorization, audit, deployment control, and business logic. The Witness is
external durable evidence authority only and never a second Control Plane.

```text
MAC_MINI_M4_CONTROL_PLANE=SOLE
CONTINUITY_WITNESS_SECOND_CONTROL_PLANE=NO
CONTINUITY_WITNESS_AUTHORITY=EXTERNAL_DURABLE_EVIDENCE_ONLY
UBUNTU_ROLE=STATELESS_INFRASTRUCTURE_WORKER
UBUNTU_AUTHORITY=ZERO
```

The Witness may own durable continuity evidence. It may not own platform
business logic, Production mutation authority, SEC-02 bootstrap authority,
release/install authority, `ControlledExecutionPort` authority, WU09 authority,
or AIControlCenter orchestration authority.

Ubuntu owns none of the Witness datastore, immutable archive, Witness signing
keys, Human Continuity Lifecycle Approver keys, lifecycle authority,
application state, business state, or continuity state. No Witness or lifecycle
operation may be routed through `UbuntuWorkerClient.execute`, a generic remote
command, or Linux systemd Control Plane artifacts. Such Linux Control Plane
artifacts remain `LEGACY_UNSUPPORTED`.

## 3. Selected deployment architecture

The selected logical deployment is a stateless external Witness application
service on AWS, external to both the governed Mac and Ubuntu.

```text
CONTINUITY_WITNESS_CLOUD_PROVIDER=AWS
CONTINUITY_WITNESS_EXTERNAL_TO_GOVERNED_MAC=YES
CONTINUITY_WITNESS_EXTERNAL_TO_UBUNTU=YES
CONTINUITY_WITNESS_APPLICATION_SERVICE=STATELESS
```

The logical architecture contains:

- HTTPS API ingress;
- a stateless Witness application runtime;
- a PostgreSQL primary transactional datastore;
- an independent rollback-resistant immutable history anchor;
- a Witness signing service; and
- a hardware-binding privacy index service.

These are logical components only. This document does not select resource
names, accounts, regions, availability zones, networking products, compute
products, PostgreSQL products, deployment tooling, service-authentication
products, DNS, certificates, scaling policy, backup schedules, or disaster-
recovery procedures. It does not claim that an AWS account or any resource has
been accessed, created, configured, or deployed.

```text
CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO
IMPLEMENTATION_READY=NO
```

## 4. PostgreSQL and rollback-resistant immutable history

PostgreSQL is the primary transactional datastore for current Witness records,
identity evaluations, approval claims, lifecycle operations, transition rows,
and exact operation results. PostgreSQL and its backups are not sufficient to
prove historical continuity: a privileged database administrator could restore
an older snapshot that omits a previously committed enrollment or transition.

The independent history anchor is append-only immutable checkpoint storage
using S3 Object Lock in Compliance mode. It is logically and evidentially
independent from PostgreSQL snapshots. Every committed lifecycle transition
must produce a new immutable checkpoint object. A prior checkpoint is never
overwritten, shortened, replaced, mutated, or treated as superseded evidence.

```text
WITNESS_ROLLBACK_RESISTANT_HISTORY_ANCHOR_REQUIRED=YES
WITNESS_ROLLBACK_RESISTANT_HISTORY_ANCHOR=S3_OBJECT_LOCK_COMPLIANCE
WITNESS_DATABASE_SNAPSHOT_ROLLBACK_MAY_PROVE_GENESIS=NO
POSTGRESQL_IS_SOLE_CONTINUITY_HISTORY_AUTHORITY=NO
IMMUTABLE_HISTORY_RETENTION_MUST_COVER_FULL_CONTINUITY_AUTHORITY_LIFETIME=YES
IMMUTABLE_HISTORY_RETENTION_EXPIRY_MAY_PROVE_GENESIS=NO
GENESIS_REQUIRES_COMPLETE_IMMUTABLE_HISTORY_COVERAGE=YES
IMMUTABLE_HISTORY_COVERAGE_UNVERIFIABLE_MAY_PROVE_GENESIS=NO
IMMUTABLE_HISTORY_RETENTION_SHORTENING_ALLOWED=NO
```

Each immutable checkpoint binds at minimum:

- protocol/schema version;
- `continuity_host_id`;
- hardware-binding privacy index;
- enrollment generation;
- record generation;
- lifecycle operation ID;
- lifecycle operation type;
- previous transition digest;
- resulting transition digest;
- maximum release version;
- maximum bootstrap trust-source version;
- lifecycle state;
- timestamp;
- Witness signing-key ID and version; and
- Witness signature.

Checkpoint publication and the PostgreSQL transaction require a future
implementation protocol that cannot report a lifecycle transition as proven
unless both exact results are durably established. This document does not claim
cross-service atomicity. Partial, ambiguous, missing, or conflicting outcomes
fail closed and create no completion or retry authority.

GENESIS evaluation must consult rollback-resistant historical evidence, not
merely current PostgreSQL state. PostgreSQL snapshot rollback, current-row
absence, local-state absence, or archive unavailability cannot establish that
hardware is unseen. PostgreSQL/immutable-history disagreement fails closed.

```text
IMMUTABLE_HISTORY_UNAVAILABLE_MAY_PROVE_GENESIS=NO
IMMUTABLE_HISTORY_CONFLICT_MAY_PROVE_GENESIS=NO
LOCAL_STATE_ABSENCE_PROVES_FIRST_INSTALL=NO
```

Retention expiry, missing historical coverage, account deletion, bucket loss,
or inability to prove complete coverage is `UNAVAILABLE` or `UNCERTAIN` and
fails closed. None is historical absence, evidence that hardware is unseen, or
evidence of first install. S3 Object Lock Compliance is the selected anchor,
but no operational retention schedule is selected or asserted implemented.

## 5. Hardware identity privacy index

The Witness uses a purpose-bound deterministic privacy-preserving index for
historical lookup of successfully validated attested hardware identity.

```text
HARDWARE_BINDING_PRIVACY_PRESERVING_INDEX_REQUIRED=YES
HARDWARE_BINDING_INDEX_PRIMITIVE=HMAC_SHA256
HARDWARE_BINDING_INDEX_KEY_CUSTODY=AWS_KMS_HMAC
HARDWARE_BINDING_INDEX_KMS_KEY_SPEC=HMAC_256
HARDWARE_BINDING_INDEX_KMS_KEY_USAGE=GENERATE_VERIFY_MAC
HARDWARE_BINDING_INDEX_MAC_ALGORITHM=HMAC_SHA_256
```

The canonical HMAC input is an RFC 8785 JCS object with an explicit hardware-
binding schema version, an exact protocol-purpose domain, the attested UDID,
and the attested serial number as separate named string fields. Field names,
types, boundaries, purpose, and version are included in and cryptographically
bound by the HMAC input; ambiguous concatenation is forbidden. Plain
`SHA-256(serial || UDID)` is forbidden.

Raw serial number and raw UDID may exist only transiently inside the bounded
attestation-validation and HMAC operation. They must not appear in URLs, S3
object keys, logs, audit event identifiers, externally visible database
indexes, metrics, traces, error messages, or durable external identifiers.
Checkpoint object keys use non-hardware-bearing opaque operation/checkpoint
identifiers; hardware lookup uses only the keyed privacy index.

The index record binds its HMAC key ID/version. Rotation must retain controlled
historical lookup using every still-required historical index-key version or a
separately frozen, ambiguity-free reindex protocol. Rotation, deletion,
disablement, or loss may never make previously enrolled hardware appear unseen
or eligible for GENESIS. Any uncertain historical lookup fails closed.

## 6. Witness signing-key custody and purpose

Witness evidence continues to use Ed25519. Its private key is a non-exportable
AWS KMS key with the Ed25519 key specification.

```text
WITNESS_SIGNING_PRIMITIVE=ED25519
WITNESS_SIGNING_KEY_CUSTODY=AWS_KMS
WITNESS_SIGNING_KMS_KEY_SPEC=ECC_NIST_EDWARDS25519
WITNESS_SIGNING_KMS_SIGNING_ALGORITHM=ED25519_SHA_512
WITNESS_SIGNING_KMS_MESSAGE_TYPE=RAW
WITNESS_SIGNING_PRIVATE_KEY_EXPORTABLE=NO
```

The Witness signing key may sign only canonical Witness protocol evidence,
including Witness response envelopes and immutable continuity checkpoints. Its
key policy, signing context, canonical domain, and schema purpose must reject
use for Human Continuity Lifecycle Approvals, SEC-02 approvals,
release/install approvals, Production execution authorization, Human Bootstrap
Approver artifacts, or any generic signature service.

```text
WITNESS_SIGNING_KEY_PURPOSE=WITNESS_PROTOCOL_EVIDENCE_ONLY
WITNESS_SIGNING_KEY_DOMAIN_SEPARATION_REQUIRED=YES
WITNESS_SIGNING_PROTOCOL_PURPOSE_DOMAIN=WITNESS_PROTOCOL_EVIDENCE
```

Historical signatures remain verifiable by durable public-key ID/version and
validity metadata. Rotation cannot reinterpret, invalidate by omission, or
silently replace historical signed evidence. Provisioning, IAM/KMS policy,
rotation, revocation, compromise recovery, trust distribution, and operational
validation remain unimplemented.

## 7. Human Continuity Lifecycle Approver key custody

The Human Continuity Lifecycle Approver uses a separate dedicated Ed25519 AWS
KMS key. It is never the Witness key and is never available to a workload or
automation principal.

```text
LIFECYCLE_APPROVAL_SIGNING_PRIMITIVE=ED25519
WITNESS_AND_LIFECYCLE_KEYS_SEPARATE=YES
LIFECYCLE_APPROVAL_SIGNING_KEY_CUSTODY=AWS_KMS
LIFECYCLE_APPROVAL_KMS_KEY_SPEC=ECC_NIST_EDWARDS25519
LIFECYCLE_APPROVAL_KMS_SIGNING_ALGORITHM=ED25519_SHA_512
LIFECYCLE_APPROVAL_KMS_MESSAGE_TYPE=RAW
LIFECYCLE_APPROVAL_SIGNING_PRIVATE_KEY_EXPORTABLE=NO
LIFECYCLE_APPROVAL_SIGNING_PRINCIPAL=HUMAN_ONLY
LIFECYCLE_APPROVAL_SIGNING_PROTOCOL_PURPOSE_DOMAIN=HUMAN_CONTINUITY_LIFECYCLE_APPROVAL
```

The dedicated lifecycle key has a separate key policy from Witness signing.
Its operational contract requires a short-lived interactive authenticated
human session with MFA. Only the human signing principal may have `kms:Sign`.
The Witness workload principal, AIControlCenter runtime principal, Ubuntu, and
all automation principals have zero permission to produce lifecycle approval
signatures. No workload principal may have `kms:Sign`; automatic signing,
delegated signing, batch signing, and reusable approval signatures are
forbidden.

One human action produces one signature over one exact evaluation-bound
approval payload for one lifecycle operation. The key cannot sign Witness
evidence, SEC-02 approvals, release/install approvals, Human Bootstrap Approver
artifacts, or Production execution authorization.

This document selects the custody architecture only. It does not claim that the
key, human principal, interactive session, MFA enforcement, IAM policy, KMS key
policy, signing interface, audit trail, provisioning, or rotation is
implemented or configured.

## 8. Signed-envelope canonicalization

All Witness evidence and lifecycle-approval signed envelopes use RFC 8785 JSON
Canonicalization Scheme. Floating-point values are prohibited. Binary values,
digests, signatures, nonces, and key identifiers represented as binary use
strict unpadded base64url with no alternate spelling accepted.

```text
SIGNED_ENVELOPE_CANONICALIZATION=RFC8785_JCS
SIGNED_ENVELOPE_FLOATS_ALLOWED=NO
SIGNED_ENVELOPE_BASE64URL=STRICT_UNPADDED
SIGNED_ENVELOPE_SCHEMA_VERSION_REQUIRED=YES
SIGNED_ENVELOPE_DOMAIN_SEPARATION_REQUIRED=YES
CANONICAL_SIGNED_ENVELOPE_MAXIMUM_BYTES=4096
LARGE_APPLICATION_PAYLOADS_SIGNED_INLINE=NO
SIGNED_ENVELOPE_BINDS_APPLICATION_PAYLOAD_DIGEST=YES
ED25519_PH_SHA_512_SELECTED=NO
```

Every signature binds an exact protocol-purpose domain, schema version,
operation ID, evaluation ID, lifecycle operation type, relevant host identity,
challenge and evidence digests, and expected transition. Where a field is not
applicable, the versioned schema must define an exact typed representation; it
may not be omitted ambiguously. Signatures never cover ambiguous concatenations
or human-readable approval strings.

AWS KMS receives the canonical signed envelope as `MessageType=RAW`, and that
envelope must be no more than 4096 bytes. Large application payloads are never
signed inline; the compact canonical envelope instead binds their cryptographic
payload digest. Witness evidence and Human Continuity Lifecycle Approval use
their distinct protocol-purpose domains and separate keys.

## 9. DeviceInformation and MDA implementation boundary

`DeviceInformation` remains an MDM/device-management-service operation and the
selected architecture transport. This document does not select an MDM product,
configure an MDM service, or execute attestation.

```text
MDA_TRANSPORT_ARCHITECTURE_DEFINED=YES
CONTINUITY_WITNESS_MDA_TRANSPORT=DEVICE_INFORMATION
MDA_DEVICE_INFORMATION_SELECTED=YES
MDA_ACME_SELECTED_FOR_CONTINUITY_WITNESS=NO
MDA_DEVICE_INFORMATION_FRESHNESS_BINDING=DEVICE_ATTESTATION_NONCE_EQUALS_ATTESTED_FRESHNESS_CODE
MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO
MDA_TRANSPORT_IMPLEMENTED=NO
MDM_VENDOR_SELECTED=NO
```

Every evaluation that requires fresh identity evidence is bound to the exact
expected challenge/freshness value. The expected `DeviceAttestationNonce` must
equal the attested freshness code. Cached, unavailable, stale, malformed, or
rate-limited attestation fails closed wherever fresh attestation is required.
It never creates automatic retry, mutation, approval, or claim-recovery
authority.

### 9.1 Exact preserved DECOMMISSION evidence contract

The committed lifecycle freeze states exactly:

> Decommission requires one exact Human Continuity Lifecycle Approval for
> `DECOMMISSION` bound to the current evaluation and record.

That is the complete prior DECOMMISSION evidence requirement. Commit `41e9f4f`
remains authoritative for DECOMMISSION lifecycle semantics and does not require
fresh MDA for DECOMMISSION. The directly conflicting fresh-valid-identity-
evidence requirement for DECOMMISSION in commit `96db578` is a documentation
overconstraint and erratum; it is non-authoritative for DECOMMISSION. This
correction restores the already-frozen baseline and introduces no new SEC-02
semantic change. GENESIS, RECOVERY, and MIGRATION fresh-evidence requirements
remain unchanged. DECOMMISSION continues to require one exact Human Continuity
Lifecycle Approval for `DECOMMISSION` bound to the current evaluation and
record, and `DECOMMISSIONED` remains terminal. Any future strengthening or
destructive re-enrollment contract requires a separate architecture freeze and
an explicit semantics change review.

```text
DECOMMISSION_LIFECYCLE_SEMANTICS_AUTHORITY_COMMIT=41e9f4f
DECOMMISSION_FRESH_MDA_REQUIRED=NO
DECOMMISSION_EXACT_HUMAN_APPROVAL_BOUND_TO_CURRENT_EVALUATION_AND_RECORD_REQUIRED=YES
DECOMMISSION_TERMINAL=YES
COMMIT_96db578_DECOMMISSION_FRESH_IDENTITY_REQUIREMENT=DOCUMENTATION_OVERCONSTRAINT_ERRATUM
COMMIT_96db578_DECOMMISSION_FRESH_IDENTITY_REQUIREMENT_AUTHORITATIVE=NO
DECOMMISSION_CORRECTION_RESTORES_ALREADY_FROZEN_BASELINE=YES
DECOMMISSION_CORRECTION_INTRODUCES_NEW_SEC02_SEMANTIC_CHANGE=NO
GENESIS_FRESH_EVIDENCE_REQUIREMENT_CHANGED=NO
RECOVERY_FRESH_EVIDENCE_REQUIREMENT_CHANGED=NO
MIGRATION_FRESH_EVIDENCE_REQUIREMENT_CHANGED=NO
```

## 10. Approval consumption and ambiguous outcomes

The existing durable-claim architecture is preserved exactly:

```text
LIFECYCLE_APPROVAL_DURABLE_CLAIM_REQUIRED=YES
DURABLY_CLAIMED_REUSABLE=NO
DURABLE_CLAIM_ITSELF_PERMANENTLY_CONSUMES_AUTHORITY=YES
TERMINALIZATION_WRITE_REQUIRED_TO_PREVENT_REUSE=NO
ROLLBACK_MAY_RESTORE_APPROVAL_AUTHORITY=NO
FAILED_CONSUMED_REUSABLE=NO
UNCERTAIN_CONSUMED_REUSABLE=NO
STRANDED_DURABLY_CLAIMED_REUSABLE=NO
CLAIM_STEALING_ALLOWED=NO
AUTOMATIC_CLAIM_RECOVERY_ALLOWED=NO
AUTOMATIC_RETRY_AUTHORITY=NO
```

An ambiguous database commit acknowledgement, checkpoint result, connection
state, or HTTP response permits read-only exact-result reconciliation only. It
never permits a mutation retry, approval reuse, claim recovery, claim stealing,
automatic completion, rollback, or compensation. Reconciled success requires
the exact expected committed operation and exact matching database and
immutable-checkpoint facts. Non-exact, absent, conflicting, malformed, or
uncertain evidence fails closed.

## 11. Closed failure model

The following conditions fail closed:

- PostgreSQL unavailable;
- immutable archive unavailable;
- immutable archive and database disagreement;
- AWS KMS unavailable;
- Witness signing failure;
- HMAC/privacy-index generation or lookup failure;
- MDA unavailable;
- stale or cached MDA where freshness is required;
- malformed Apple attestation;
- challenge or freshness mismatch;
- invalid lifecycle approval;
- ambiguous transaction commit;
- ambiguous HTTP response; and
- cloud account or resource uncertainty.

None may become `GENESIS_ELIGIBLE`, prove historical absence, restore consumed
authority, or create retry authority. Archive/account/bucket loss is
`UNAVAILABLE`; database/archive conflict is `UNCERTAIN`; malformed evidence is
`MALFORMED`; and exact classifications remain subject to the existing closed
protocol vocabulary. A failure classification is evidence only and grants zero
mutation, install, bootstrap, SEC-02, release, execution, recovery, rollback,
or retry authority.

## 12. Preserved unresolved operational state

The architecture-level reset-attack resolution remains frozen, while the
operational reset attack, implementation, MDA realization, and Production
bootstrap remain unresolved.

```text
FIRST_INSTALL_RESET_ATTACK_ARCHITECTURE_RESOLVED=YES
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO
KEY_CUSTODY_IMPLEMENTATION_DEFINED=NO
MDA_TRANSPORT_IMPLEMENTATION_DEFINED=NO
MDA_TRANSPORT_IMPLEMENTED=NO
MDM_VENDOR_SELECTED=NO
CONTINUITY_WITNESS_CLOUD_HOST_SELECTED=NO
CONTINUITY_WITNESS_INGRESS_TOPOLOGY_DEFINED=NO
IMPLEMENTATION_READY=NO
SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY
BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
```

No Witness runtime, PostgreSQL datastore, S3 immutable archive, AWS KMS key,
HMAC service, MDM integration, ingress, network, account, policy, backup,
restore procedure, or disaster-recovery capability is asserted to exist.

## 13. Architecture consistency gates

```text
SEC02_CONTINUITY_WITNESS_DEPLOYMENT_KEY_CUSTODY_ARCHITECTURE_FROZEN=YES
AWS_DEPLOYMENT_ARCHITECTURE_SELECTION_GATE=PASS_SELECTED_NOT_PROVISIONED
STATELESS_WITNESS_APPLICATION_GATE=PASS_LOGICAL_ARCHITECTURE_ONLY
ROLLBACK_RESISTANT_HISTORY_GATE=PASS_S3_OBJECT_LOCK_COMPLIANCE_REQUIRED
POSTGRESQL_SNAPSHOT_GENESIS_GATE=PASS_DENIED
IMMUTABLE_HISTORY_UNAVAILABLE_GENESIS_GATE=PASS_DENIED
IMMUTABLE_HISTORY_RETENTION_GATE=PASS_FULL_AUTHORITY_LIFETIME_REQUIRED
HARDWARE_IDENTITY_PRIVACY_GATE=PASS_HMAC_SHA256_AWS_KMS_HMAC
HMAC_INDEX_CONTRACT_GATE=PASS_HMAC_256_GENERATE_VERIFY_MAC_HMAC_SHA_256
RAW_HARDWARE_EXTERNAL_IDENTIFIER_GATE=PASS_PROHIBITED
WITNESS_SIGNING_CUSTODY_GATE=PASS_AWS_KMS_NON_EXPORTABLE_ED25519_SELECTED
KMS_SIGNING_CONTRACT_GATE=PASS_ED25519_SHA_512_RAW_MAX_4096_BYTES
LIFECYCLE_APPROVAL_CUSTODY_GATE=PASS_HUMAN_ONLY_AWS_KMS_ED25519_SELECTED
WITNESS_LIFECYCLE_KEY_SEPARATION_GATE=PASS
WORKLOAD_HUMAN_APPROVAL_SIGNING_GATE=PASS_ZERO_PERMISSION
SIGNED_ENVELOPE_CANONICALIZATION_GATE=PASS_RFC8785_JCS
DECOMMISSION_SEMANTICS_GATE=PASS_41e9f4f_AUTHORITATIVE_96db578_ERRATUM_NONAUTHORITATIVE
APPROVAL_CONSUMPTION_GATE=PASS_PERMANENT_AT_DURABLE_CLAIM
AMBIGUOUS_RESULT_GATE=PASS_READ_ONLY_EXACT_RECONCILIATION_ONLY
FAIL_CLOSED_GENESIS_GATE=PASS
IMPLEMENTATION_READY=NO
```

## 14. Change and activity attestation

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
AWS_API_ACCESSED=false
CLOUD_RESOURCE_CREATED=false
AWS_CREDENTIALS_ACCESSED=false
GIT_MUTATION=false
```

`GIT_MUTATION=false` means no staging, commit, push, reset, branch rewrite, or
other Git-state mutation is authorized or performed. The requested architecture
document is a working-tree filesystem addition only.
