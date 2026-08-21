# MACRO-WU-06 Trusted Ownership Expectation Architecture Contract

## 1. Status and scope

`ARCHITECTURE_DISCOVERY_GATE=PASS` and this architecture is frozen:

```text
TRUSTED_OWNERSHIP_EXPECTATION_ARCHITECTURE_FROZEN=true
TRUSTED_UID_SOURCE_ARCHITECTURE_FROZEN=true
TRUSTED_GID_SOURCE_ARCHITECTURE_FROZEN=true
```

This is documentation-only architecture work. It defines a future repository
issuer and value but does not implement or execute either, establish an
operational GID source, inspect a filesystem target, access protected evidence,
or access Production.

## 2. Existing authoritative identity facts

The repository already implements and validates `RuntimeHomeResolver` and its
immutable, slotted `ResolvedTrustedMacAccountHome` result. The resolver remains
the only supported repository runtime path that establishes `bound_uid`:

```text
exact Darwin
-> one real UID observation
-> one effective UID observation
-> both non-root
-> exact equality
-> bind UID
-> exactly one pwd.getpwuid(bound_uid)
```

The ownership expectation issuer consumes an already-existing resolved result.
Resolver and issuer remain separate boundaries.

## 3. Exact UID source

The rule is exactly:

```text
expected_uid = ResolvedTrustedMacAccountHome.bound_uid
```

The issuer reuses that fact and performs zero additional UID or passwd
observations. It must not construct or execute `RuntimeHomeResolver`, call
`platform.system()`, `os.getuid()`, or `os.geteuid()`, execute another
`pwd.getpwuid()`, accept a caller UID, or accept UID authority from environment,
`HOME`, argv, or JSON.

## 4. Exact repository-owned group policy

The repository-owned Mac Control Plane application-group policy is exactly:

```text
TRUSTED_APPLICATION_GROUP_NAME="staff"
```

It is fixed policy, not caller-selectable input. No environment, `HOME`, argv,
JSON, candidate list, or other external input may replace it.

## 5. Exact GID resolution rule

The issuer performs exactly one logical lookup:

```text
grp.getgrnam("staff")
```

It uses only the returned `gr_gid` as `expected_gid`. The maximum group lookup
count is one. It must not use `os.getgid()`, `os.getegid()`, ambient process
GID, supplementary groups, caller-selected group or GID, passwd `pw_gid`,
`wheel`, group enumeration, candidate groups, alternate groups, retry,
fallback, or best-effort matching.

## 6. Lookup budget and ordering

The complete ordered logical chain is frozen without merging boundaries:

1. Existing `RuntimeHomeResolver`, within its already-implemented boundary:
   `platform.system()` maximum one, `os.getuid()` maximum one,
   `os.geteuid()` maximum one, and `pwd.getpwuid(bound_uid)` maximum one.
2. Future `TrustedOwnershipExpectation` issuer: consume the already-resolved
   `ResolvedTrustedMacAccountHome`, perform zero additional UID observations,
   zero additional passwd lookups, and at most one
   `grp.getgrnam("staff")` lookup.

The resolved home must exist before issuer evaluation; a successful exact group
lookup and validation must exist before the value can be issued.

## 7. Fail-closed behavior

The group boundary fails closed on any lookup exception, missing `gr_gid`,
wrong exact type, negative GID, or otherwise malformed result. `gr_gid` must
have exact type `int`; subclasses and coercion are rejected. Failure produces
no expectation and grants no positive fact or authority. No retry, fallback,
second lookup, enumeration, alternate group, or recovery is permitted.

## 8. TrustedOwnershipExpectation value shape

The future `TrustedOwnershipExpectation` is immutable, slotted, factual,
zero-authority, and has the minimum exact two-field data shape:

```text
expected_uid: int
expected_gid: int
```

No additional data field, provenance token, authority marker, path, metadata,
or evidence field belongs to this value.

## 9. Zero-authority semantics

`TrustedOwnershipExpectation` is not unforgeable provenance, authorization,
capability, admission evidence, verification evidence, filesystem existence
evidence, filesystem safety evidence, metadata evidence, `RECOVER` evidence
sufficiency, Production authorization, Production readiness, or a security
boundary. Possession or Python object identity grants zero authority.
Downstream security-sensitive boundaries independently validate every required
fact, item of evidence, and authority.

## 10. Semantic separation

The following concepts remain exactly distinct:

```text
TrustedMacAccountHomePolicy
!= RuntimeAccountIdentityObservation
!= RuntimeHomeResolver
!= ResolvedTrustedMacAccountHome
!= TrustedApplicationGroupPolicy
!= TrustedOwnershipExpectation
!= ConcreteProtectedEvidencePath
!= FilesystemTargetMetadataSnapshotRequest
!= FilesystemTargetMetadataSnapshot
!= SourceExistence
!= MetadataInspection
!= MetadataSafety
!= ContentAcquisition
!= EvidenceAdmission
!= EvidenceVerification
!= Authority
```

Architecture selection, repository value construction, filesystem observation,
evidence, and authority are not interchangeable.

## 11. Filesystem dependency ordering

The future dependency order is:

```text
ConcreteProtectedEvidencePath
+
TrustedOwnershipExpectation
->
FilesystemTargetMetadataSnapshotRequest
->
at most one exact-target lstat
```

`TrustedOwnershipExpectation` must exist before the future request can make any
positive ownership comparison. This step does not implement the request,
snapshot, or adapter.

## 12. Single-lstat preservation

The existing filesystem observation count remains `0..1`: exactly one `lstat`
of the exact unchanged concrete target after complete request validation, or
zero observations when validation fails. There is no `stat`, parent walk, leaf
lookup, `exists`, `is_dir`, `is_file`, `is_symlink`, second metadata
observation, retry, fallback, recovery, candidate iteration, directory
enumeration, open, or read.

Successful directory metadata classification remains exactly
`DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`, never `SAFE_BOUND` or
`METADATA_SAFE_AND_STABLY_BOUND`. It remains a point-in-time snapshot with:

```text
stable_handle_bound=false
TOCTOU_CLOSED=false
FD_INODE_DEVICE_BOUND=false
```

No stable target, race closure, open-file binding, or acquisition safety is
claimed.

## 13. Control Plane and Governance separation

Mac AIControlCenter remains the sole Control Plane. Ubuntu has zero role and
zero authority. Governance and SEC-02 are unchanged.
`ControlledExecutionPort` remains uncoupled. Mutation budget remains zero.
This architecture grants no execution, deployment, admission, Production, or
filesystem authority.

## 14. Preserved program state

Architecture selection is not operational establishment. The preserved state
is exactly:

```text
RUNTIME_HOME_RESOLVER_REPOSITORY_IMPLEMENTED=true
RUNTIME_HOME_RESOLVER_REPOSITORY_VALIDATED=true
CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_IMPLEMENTED=true
CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_VALIDATED=true
OPERATIONAL_TRUSTED_OWNERSHIP_EXPECTATION_ISSUER_IMPLEMENTED=false
TRUSTED_GID_SOURCE_ESTABLISHED=false
TRUSTED_HOME_VALUE_ESTABLISHED=false
ABSOLUTE_PATH_ESTABLISHED=false
CONCRETE_PATH_VALUE_ESTABLISHED=false
FILESYSTEM_IO_PERFORMED=false
PROTECTED_SOURCE_ACCESS_PERFORMED=false
PRODUCTION_ACCESS_PERFORMED=false
RECOVER_EVIDENCE_SUFFICIENT=false
OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN
RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT
SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```

## 15. Explicit next implementation boundary

Only after architecture Git closeout, the next milestone is separately gated:

```text
MACRO_WU_06_TRUSTED_OWNERSHIP_EXPECTATION_IMPLEMENTATION
```

That milestone must implement and validate only the repository-owned issuer and
exact two-field value under this contract. It remains unchecked. This freeze
does not claim the issuer implemented or the trusted GID source operationally
established, and it does not authorize the filesystem snapshot request or
adapter, protected-source access, or Production access.
