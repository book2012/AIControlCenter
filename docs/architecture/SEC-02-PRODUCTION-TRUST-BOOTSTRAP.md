# SEC-02 Production Trust Bootstrap Architecture Freeze

Status: **FROZEN**

```text
SEC02_PRODUCTION_TRUST_BOOTSTRAP_ARCHITECTURE_FREEZE=COMPLETE
```

## 1. Decision and scope

This document freezes the architecture for the first creation of the SEC-02
Production human-issuer trust registry. It is documentation only. It creates no
Production authority, trust material, signing key, executable bootstrap path, or
authorization.

The existing generic Trusted Authorization Intake, SEC-02 semantics, Governance
core, `ControlledExecutionPort`, and WU09 remain unchanged. Authenticity is not
execution authority, and authorization consumption is not execution authority.

The invariant remains:

```text
Human Issuer
-> immutable signed authorization artifact
-> Generic Trusted Authorization Intake
-> existing SEC-02
-> feature-specific ControlledExecutionPort
```

Issuer, intake, operator, and executor are distinct authority boundaries.

## 2. Bootstrap paradox and resolution

The ordinary Trusted Authorization Intake authenticates signed authorization
artifacts against the Production trust registry. When that registry is absent,
it cannot authenticate an artifact that purports to authorize creation of the
same registry. Requiring ordinary SEC-02 intake for the first registry would be
circular; accepting the prospective issuer's signature would be
self-registration. Existing SEC-02 is therefore **not sufficient by itself** to
authorize initial trust-root creation.

The frozen resolution is a separate, one-time local bootstrap authority. It is a
new future implementation boundary with exactly one capability: atomically
create the initially absent registry from independently approved public
verification facts on the Mac Control Plane. It is not a generic executor, is
not part of Trusted Authorization Intake, and grants no authority to execute a
feature action.

The authority is established by a bounded, human-controlled bootstrap ceremony,
an immutable signed bootstrap approval, and a dedicated **PRECONFIGURED
BOOTSTRAP APPROVER VERIFICATION TRUST** boundary. Repository review found no
existing generic verification authority that can be reused for this purpose.
The new boundary is therefore a prerequisite of the future implementation.

The bootstrap approval public verification key, its key identifier, algorithm,
and approved Human Bootstrap Approver identity are immutable release inputs
installed from a separately governed Control-Plane release trust source. They
are not fields in the local authorization record, registry proposal, API/CLI
request, environment, argv, or library call. The release trust source must be
authenticated and integrity-bound under the separately reviewed release process
before bootstrap begins; a locally created or replaced file is not such a
source. Production holds only this public verification material. The
corresponding private key remains offline in the sole custody of the Human
Bootstrap Approver and must never enter Production.

The locally provisioned, single-use record contains the immutable signed
approval and exact registry bindings. The bootstrap verifier selects the
preconfigured approver public key by the preconfigured key identifier, verifies
an Ed25519 signature over the complete RFC 8785 canonical approval prefixed by
the dedicated domain separator
`AICONTROLCENTER-SEC02-TRUST-BOOTSTRAP-APPROVAL-V1` and one NUL byte, and
verifies that the
signed approver identity and all proposed registry facts and digest exactly
match the preconfigured identity and create request. Unknown keys, alternate
keys, caller-provided keys, missing or altered bindings, signature failure, or
release-trust ambiguity fail closed before consumption or mutation. The
record's provenance is independent of:

- the issuer or key being registered;
- the operator invoking the bootstrap command;
- any authorization artifact being verified;
- WU09 or any other feature;
- Ubuntu; and
- a caller of an API, CLI, or library.

The **Human Bootstrap Approver** must be an approval identity independent of the
prospective Human Issuer and the local operator. The future implementation must
validate that identity separation and the offline approval-to-local-record
provisioning ceremony against the preconfigured verification trust above. It
must not infer bootstrap authority merely from
possession of an issuer private key, local login, UID/GID, command invocation,
artifact contents, or registry payload. Until that implementation and ceremony
are validated, Production bootstrap is unavailable and registry absence fails
closed.

This primitive does not weaken or extend SEC-02. It exists only before the trust
root can support authenticated authorization intake and becomes permanently
unusable after its single terminal consumption.

## 3. Authority boundaries and private-key custody

Production AIControlCenter must never generate, store, serialize, log, receive,
or expose an issuer or bootstrap-approver private signing key. Private issuer
keys remain entirely inside the Human Issuer boundary; the bootstrap-approver
private key remains offline inside the Human Bootstrap Approver boundary.
The proposed-registry portion of bootstrap input and the Production registry
may contain only:

- `issuer_id`;
- `issuer_type` and other bounded issuer metadata;
- `key_id`;
- an Ed25519 public key;
- validity bounds;
- status and optional revocation state; and
- the required registry bindings and integrity fields.

The issuer cannot approve or register itself. The operator can perform local OS
actions only after independent bootstrap authorization has been established;
operator identity cannot manufacture approval authority. A generic caller
cannot inject a username, UID, GID, platform, trust path, issuer approval, or
bootstrap authority.

The signed approval additionally binds its schema version, approver identity,
preconfigured approver key identifier, issuance and expiry times, unique
bootstrap authorization identifier, intended Control Plane and operation
(`INITIAL_CREATE` only), every proposed-registry field, and the deterministic
proposed registry digest. The detached signature is outside that protected
object. No unsigned field may drive verification, ownership, path selection,
consumption, or creation.

## 4. Trust-root location and path authority

The sole logical Production registry path remains:

```text
<trusted_passwd_home>/Library/Application Support/AIControlCenter/governance/trust/sec02-human-issuers.v1.json
```

Two distinct facts must not be conflated:

1. **Runtime OS identity and home observation.** On Darwin, the process requires
   `ruid == euid`, requires the observed identity to be non-root, and uses
   `pwd.getpwuid(ruid)` solely to observe the runtime account and derive its
   passwd home.
2. **Expected protected-asset ownership.** Expected UID and GID for the trust
   directory, temporary file, and registry are trusted policy inputs from a
   generic **PRECONFIGURED CONTROL PLANE OWNERSHIP AUTHORITY**, independently
   governed and immutable for the operation. Runtime UID/GID observations are
   compared with those expected values; they do not create them.

Repository review found no suitable generic preconfigured ownership authority.
The current SEC-02 freeze and `trust/path_policy.py` instead derive expected UID
and GID from the bound Darwin passwd record; the existing ownership-expectation
module is Shopping/MariaDB-specific and is not reusable here. Therefore the
generic preconfigured ownership authority and its reconciliation with the
committed SEC-02 trust-path invariant are an explicit prerequisite to bootstrap
implementation. This document neither silently redefines that committed
invariant nor authorizes a SEC-02 or current path-policy change.

The path and identity must never derive from `HOME`, `Path.home()`, environment
variables, argv, caller-supplied username, caller-supplied UID/GID,
caller-supplied platform, or caller-supplied trust path. Unrelated ancestors,
including `/` and `/Users`, need not be owned by the Control Plane user. The
protected trust directory and registry leaf are governed by the exact checks in
this freeze.

## 5. Initial creation ceremony

Initial creation is exactly:

```text
ABSENT
-> independently validated one-time bootstrap authorization
-> read-only local preconditions
-> exactly one bounded atomic registry-create attempt
-> read-only postcondition verification
-> durable evidence
-> permanently sealed bootstrap path
```

The high-level ceremony is:

1. A Human Bootstrap Approver, distinct from the prospective issuer and local
   operator, reviews and approves the exact issuer public verification facts and
   deterministic proposed registry digest.
2. The separate bootstrap boundary validates an independently provisioned,
   single-use local bootstrap authorization record and its exact bindings. The
   record is not authenticated by the absent registry and cannot authorize any
   other mutation.
3. AIControlCenter verifies the preconfigured bootstrap-approver trust anchor,
   signed approval, identity separation, and exact approval bindings, then
   performs read-only Darwin identity, path, absence, ownership, mode, payload,
   digest, and authorization preconditions.
4. Before attempting the mutation, it durably consumes the one-time bootstrap
   authorization. Consumption authorizes at most one create attempt, not a
   successful outcome and not a retry.
5. The dedicated bootstrap creator performs exactly one bounded atomic creation.
6. AIControlCenter performs read-only verification of the final file and writes
   durable, non-secret evidence of authorization consumption and outcome.
7. Whether the attempt is successful, failed, or uncertain, the authorization is
   permanently consumed. On verified success the lifecycle is sealed and the
   initial-bootstrap entry point is permanently unavailable.

The create operation must fail closed before mutation if the registry exists.
It must use create-if-absent semantics and must never overwrite or replace an
existing registry. There is no automatic retry, claim stealing, lease recovery,
stranded-claim recovery, automatic rollback authority, or consumed-bootstrap-
authorization reuse. A failed or uncertain attempt requires human investigation;
it does not restore bootstrap authority.

## 6. Bootstrap lifecycle

The durable successful lifecycle is:

```text
UNINITIALIZED
-> AUTHORIZED
-> CONSUMED
-> CREATE_ATTEMPTED
-> VERIFIED
-> SEALED
```

`UNINITIALIZED` means the registry is absent and no usable bootstrap authority
is established. `AUTHORIZED` binds one independent approval to one exact initial
registry body and digest. `CONSUMED` is the durable consumption state
that precedes mutation. `CREATE_ATTEMPTED` records the sole permitted mutation
attempt. `VERIFIED` requires read-only verification of the created registry.
`SEALED` permanently disables the initial-bootstrap capability.

The durable terminal branches are:

```text
CONSUMED -> FAILED_CONSUMED
CONSUMED -> CREATE_ATTEMPTED -> FAILED_CONSUMED
CONSUMED -> CREATE_ATTEMPTED -> UNCERTAIN_CONSUMED
CREATE_ATTEMPTED -> VERIFIED -> UNCERTAIN_CONSUMED
```

`FAILED_CONSUMED` means failure is known and the capability remains consumed.
`UNCERTAIN_CONSUMED` means whether mutation or durable acknowledgement occurred
cannot be proven. Both are terminal. Neither may transition to `AUTHORIZED`,
accept a new initial-bootstrap authorization, retry, restore authority, or use
cleanup as a reason to retry. Any recovery is a separate future architecture
milestone with new human governance; no recovery authority exists here.

Failure and uncertainty are terminal consumed outcomes, not transitions back to
`AUTHORIZED`. If a registry exists in any state other than the verified result
of this ceremony, bootstrap fails closed and requires a separately designed,
human-authorized recovery milestone. No recovery semantics are granted here.

The durable seal must not depend only on registry presence. Future
implementation must preserve independent durable evidence that the one-time
authority was consumed and must refuse initial bootstrap whenever the registry
already exists, the lifecycle is consumed/sealed, or the state is ambiguous.
Specifically:

- durable consumption without an acknowledged mutation is
  `UNCERTAIN_CONSUMED` and fails closed;
- an unexpectedly existing registry fails closed without publication;
- an existing registry with ambiguous durable bootstrap state fails closed and
  is never adopted, replaced, or treated as authorization evidence; and
- a registry that verifies when durable `SEALED` recording is ambiguous is
  `UNCERTAIN_CONSUMED`; verification does not restore authority or permit seal
  replay.

## 7. Atomic filesystem creation requirements

The future dedicated creator must preserve the existing descriptor-relative,
no-follow trust-path policy and enforce all of the following:

- Darwin only, with `ruid == euid` and a non-root bound identity;
- passwd-record-derived runtime identity and home, separately compared with the
  preconfigured expected ownership authority required by Section 4;
- protected trust directory exact mode `0700` and exact trusted ownership;
- final registry exact mode `0600` and exact trusted ownership;
- no symlink traversal for any governed component;
- descriptor-relative traversal and open operations with no-follow semantics;
- no pathname re-resolution after descriptor validation;
- a strict bounded registry size;
- strict validation of the exact proposed content before mutation;
- a temporary regular file created exclusively inside the protected directory;
- complete write, exact mode/ownership checks, and file `fsync`;
- exactly one descriptor-relative atomic no-replace publication within the same
  directory, precisely:

  ```c
  renameatx_np(
      trust_dir_fd,
      temporary_leaf,
      trust_dir_fd,
      final_leaf,
      RENAME_EXCL
  )
  ```

  or an exactly equivalent separately reviewed Darwin primitive;
- directory `fsync` after publication;
- read-only verification of final inode, device identity, ownership, mode,
  bounded content, canonical form, and digest; and
- fail-closed handling of every mismatch, race, unsupported primitive, or
  ambiguous outcome.

The trusted directory FD must remain the authority for both source and
destination; neither leaf may be re-resolved through an absolute or parent
pathname after directory validation. `RENAME_EXCL` must prove that the
destination did not exist at the atomic publication point. An ordinary or
clobbering rename fallback is prohibited. If the exclusive primitive is
unsupported, publication fails closed before attempting publication. The call is
made at most once. Any ambiguous return or acknowledgement becomes
`UNCERTAIN_CONSUMED`; it must not be retried. After acknowledged publication,
the final directory is `fsync`ed and the final registry is opened and verified
read-only. Temporary-file cleanup may remove only an unambiguously identified
unpublished temporary inode; it grants no authority to alter the final path or
retry publication.

## 8. Registry content and cryptographic compatibility

The already validated registry semantics and canonicalization/signature profile
remain unchanged. The registry contains `schema_version`, `registry_version`,
and `registry_digest`. Each issuer entry binds at least:

- `issuer_id`;
- `issuer_type`;
- `key_id`;
- `algorithm`, exactly `Ed25519`;
- the public key;
- status;
- `not_before` and `not_after`;
- optional `revocation_effective_at`; and
- the applicable `registry_version` binding.

The registry digest remains deterministic canonical SHA-256 over the defined
registry body excluding the top-level `registry_digest`. This freeze introduces
no alternate canonicalization, signature, key-selection, or fallback profile.

## 9. Future registry updates

Initial bootstrap and subsequent registry mutation are separate operations.
The one-time bootstrap capability cannot rotate, revoke, add, remove, or replace
issuers or keys after initial creation.

Every future registry change must be implemented under a separate milestone and
must require its own explicit human authorization, exact old-state and new-state
bindings, deterministic digest, atomic same-directory replacement, read-only
postcondition verification, and durable evidence. It must fail closed on stale
state or ambiguity. There is no automatic key replacement, silent rotation,
discovery, enrollment, fallback public key, or authorization reuse. These update
semantics are frozen requirements only and are not implemented or authorized by
this document.

## 10. Operator identity and Control Plane placement

Local OS operator identity observation and authorization/approval identity are
separate concerns. The repository's local trusted Mac identity observation may
establish who invoked a local operation; it does not prove who approved it and
does not confer bootstrap authority. This freeze does not claim that Production
operator identity composition is complete.

The Mac mini M4 is the sole Control Plane and the only permissible host for the
bootstrap authorization record, ceremony validation, registry mutation,
postcondition verification, sealing, and durable evidence. Ubuntu has zero
trust, governance, business-logic, application-state, bootstrap, approval,
verification, intake, consumption, or execution authority. Bootstrap must not
be routed through `UbuntuWorkerClient.execute`, Docker, Linux systemd, a generic
remote command, or a generic executor.

## 11. SEC-02 and WU09 relationship

Initial bootstrap is not a feature execution and does not pass through the
ordinary signed-authorization intake that depends on the registry. After the
trust root is created, verified, sealed, implemented, and operationally
validated, ordinary Production actions remain subject to the unchanged flow:

```text
trusted signed authorization
-> durable SEC-02 authorization consumption
-> fresh read-only preconditions
-> exact current-state comparison
-> rerun existing SEC-02
-> require ALLOW_SINGLE_INVOCATION
-> exactly one feature-specific ControlledExecutionPort invocation
```

`FAILED` or `UNCERTAIN` permanently consumes an ordinary authorization. There is
no automatic retry, consumed-authorization reuse, claim stealing, lease
recovery, stranded-claim recovery, or automatic rollback authority.

WU09 remains untouched. Only after Production trust bootstrap is operationally
validated may a separate WU09 milestone compose the ordinary flow above with
one bounded preload action. This freeze does not preload an image, deploy an
adapter, access Docker, or grant WU09 authority.

## 12. Review gates and implementation boundary

Architecture review records:

```text
BOOTSTRAP_PARADOX_RESOLVED=YES
BOOTSTRAP_APPROVER_TRUST_ANCHOR_DEFINED=YES
BOOTSTRAP_APPROVER_PRIVATE_KEY_ON_PRODUCTION=NO
OPERATOR_CAN_MANUFACTURE_BOOTSTRAP_AUTHORITY=NO
ISSUER_CAN_SELF_REGISTER=NO
CALLER_CAN_INJECT_BOOTSTRAP_AUTHORITY=NO
RUNTIME_IDENTITY_AND_EXPECTED_OWNERSHIP_SEPARATED=YES
FAILED_BOOTSTRAP_RETRY_ALLOWED=NO
UNCERTAIN_BOOTSTRAP_RETRY_ALLOWED=NO
INITIAL_BOOTSTRAP_AUTHORITY_RESTORED_AFTER_CONSUMPTION=NO
RECOVERY_REQUIRES_SEPARATE_ARCHITECTURE=YES
ATOMIC_NO_REPLACE_PRIMITIVE_DEFINED=YES
CLOBBERING_RENAME_FALLBACK_ALLOWED=NO
ISSUER_SELF_REGISTRATION_ALLOWED=NO
OPERATOR_SELF_AUTHORIZATION_ALLOWED=NO
CALLER_AUTHORITY_INJECTION_ALLOWED=NO
PRODUCTION_PRIVATE_KEYS_ALLOWED=NO
MAC_ONLY_BOOTSTRAP_AUTHORITY=YES
UBUNTU_AUTHORITY=ZERO
WU09_CHANGE_REQUIRED_NOW=NO
GENERIC_EXECUTOR_ALLOWED=NO
SEC02_SEMANTICS_CHANGE_REQUIRED=NO
GOVERNANCE_CORE_CHANGE_REQUIRED=NO
CONTROLLED_EXECUTION_PORT_CHANGE_REQUIRED=NO
WU09_CHANGE_REQUIRED=NO
INITIAL_MUTATION_BUDGET=ONE_CREATE_ATTEMPT
INITIAL_BOOTSTRAP_PERMANENTLY_SEALED_AFTER_SUCCESS=YES
```

The next implementation milestone is
`SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION`. It must implement and test the
separate one-time local bootstrap authority, independent approval record and
identity separation, durable lifecycle/consumption/seal, dedicated atomic
create-if-absent filesystem capability, read-only verification, and durable
evidence. That milestone must not modify SEC-02 semantics, Governance core, or
`ControlledExecutionPort`, and must remain non-Production until separately
reviewed and operationally validated.
