# AI Home Datacenter Architecture

## Current authoritative boundary — Macro-WU09 governance identity binding correction

The preload implementation at `IMPLEMENTATION_COMMIT=e179fb0` was followed by
`WU09_IDENTITY_BINDING_CORRECTION=COMPLETE` at
`IDENTITY_BINDING_CORRECTION_COMMIT=9e7a4a2`. The correction changed exactly
`ops/macos/shopping/wu09_image_preload.py` and
`tests/test_macro_wu09_pinned_image_preload.py`.

The corrected `GovernanceIdentity` boundary is explicitly keyword-bound:
requester is `identity_id=<requester identity>`, `identity_type=HUMAN`;
approver is `identity_id=<approver identity>`, `identity_type=HUMAN`; and the
Mac Control Plane collector/target is `identity_id=MAC_MINI_M4`,
`identity_type=CONTROL_PLANE`.

Authoritative correction evidence is `CANONICAL_GATE=PASS`,
`CANONICAL_RESULT=4130_PASSED_5_DESELECTED`, `CANONICAL_WARNINGS=587`, and
`CANONICAL_RC=0`; canonical was not run in this documentation-only closeout.
The correction preserves `GOVERNANCE_IDENTITY_DOMAIN_CHANGED=false`,
`GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`, and
`CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGED=false`.

No execution or authorization state changed: `WU09_PRELOAD_EXECUTED=false`,
`WU09_DEPLOYED=false`, `WU09_DEPLOYMENT_AUTHORIZED=false`,
`WU10_AUTHORIZED=false`, `WU11_AUTHORIZED=false`, and
`WU09_PRELOAD_PRODUCTION_AUTHORIZATION_CONSUMED=false`.
`TRUSTED_SEC02_PRODUCTION_HUMAN_ISSUER_EXISTS=false`,
`TRUSTED_AUTHORIZATION_ARTIFACT_BOUNDARY_REQUIRED=true`, and
`PRODUCTION_COMPOSITION_READY=false`. The pinned image is not asserted present
in Production. The next architecture milestone is
`WU09_TRUSTED_PRODUCTION_AUTHORIZATION_INTAKE_FREEZE`; the next Production
readiness milestone is
`WU09_PINNED_IMAGE_PRELOAD_PRODUCTION_COMPOSITION_READY`.

## Current authoritative boundary — Macro-WU09 governed pinned-image preload

`WU09_PINNED_IMAGE_PRELOAD_IMPLEMENTATION=COMPLETE`, following
`FREEZE_COMMIT=c15c976` at `IMPLEMENTATION_COMMIT=e179fb0`. Validation recorded
`FOCUSED_TEST_GATE=PASS`, `FOCUSED_TEST_RESULT=30_PASSED`,
`CANONICAL_GATE=PASS`, `CANONICAL_RESULT=4129_PASSED_5_DESELECTED`, and
`CANONICAL_WARNINGS=579`.

The bounded capability is
`EXACT_ACTION_TYPE=SHOPPING_MARIADB_LOOPBACK_IMAGE:PRELOAD_EXACT`, fixed to
`EXACT_DOCKER_CONTEXT=colima-aicontrolcenter-commerce` and
`EXACT_IMAGE=alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1`.
There is no generic Docker executor, caller-supplied argv, context, image, tag,
or digest, shell, retry, or fallback. Preload authorization permits exactly one
bounded preload invocation and is a separate Production mutation from WU09
deployment; it grants no deployment authority. WU09 deployment requires a
fresh later human authorization.

Repository state is `IMPLEMENTED=true`, `PRELOAD_EXECUTED=false`, and
`WU09_DEPLOYED=false`. `PRODUCTION_ACCESS_PERFORMED=false`,
`PRODUCTION_MUTATION_PERFORMED=false`, and
`WU09_PRELOAD_PRODUCTION_AUTHORIZATION_CONSUMED=false`. The pinned image is not asserted to
be present in Production. `WU09_DEPLOYMENT_AUTHORIZED=false`,
`WU10_AUTHORIZED=false`, and `WU11_AUTHORIZED=false`.

The capability performs no database mutation, network mutation, credential
access, MariaDB connection, or SQL. `GOVERNANCE_CORE_CHANGED=false`,
`SEC_02_CHANGED=false`, and
`CONTROLLED_EXECUTION_PORT_SEMANTICS_CHANGED=false`. The Mac remains the sole
Control Plane (`MAC_CONTROL_PLANE=true`); Ubuntu remains zero-authority
(`UBUNTU_AUTHORITY=false`).

## Current authoritative boundary — Macro-WU09 Production-targeting correction

`WU09_PRODUCTION_TARGETING_CORRECTION=COMPLETE` at
`CORRECTION_COMMIT=efdcc5e2da5aee821f28be43011fa08f63e5373d`.
The execution boundary explicitly fixes
`DOCKER_CONTEXT=colima-aicontrolcenter-commerce`:
`DOCKER_CONTEXT_EXPLICIT_BINDING=true` and `ACTIVE_CONTEXT_INDEPENDENCE=true`.
It also invokes `--pull never`, so `IMPLICIT_IMAGE_PULL_DISABLED=true`.

The exact Production topology remains project `ai-shopping-mariadb-loopback`,
service `mariadb-loopback-adapter`, bind `127.0.0.1:58083`, target
`database:3306`, and network `ai-shopping-internal`. Corrected validation is
`FOCUSED_RESULT=19_PASSED`, `CANONICAL_RESULT=4095_PASSED_5_DESELECTED`, and
`CANONICAL_WARNINGS=575`.

This is an implementation correction, not deployment:
`IMPLEMENTED=true`, `DEPLOYED=false`,
`HOST_PORT_ACTIVE_IN_PRODUCTION=false`, `PRODUCTION_ACCESS_PERFORMED=false`,
`PRODUCTION_MUTATION_PERFORMED=false`, and
`PRODUCTION_AUTHORIZATION_CONSUMED=false`. WU10 and WU11 remain separate and
unauthorized. `GOVERNANCE_CORE_CHANGED=false`, `SEC_02_CHANGED=false`, and
`CONTROLLED_EXECUTION_PORT_COUPLED=false`. The Control Plane boundary remains
`MAC_CONTROL_PLANE=true` and `UBUNTU_AUTHORITY=false`. Recovery remains
`RECOVER_EVIDENCE_SUFFICIENT=false` and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

## Current authoritative boundary — Macro-WU09 implemented, not deployed

Macro-WU09 repository implementation is complete at
`IMPLEMENTATION_COMMIT=815d3d5`, after architecture freeze commit `6d31afe`.
The canonical gate passed: `4093_PASSED_5_DESELECTED`, with 567 warnings.

The desired adapter topology is project `ai-shopping-mariadb-loopback`, service
`mariadb-loopback-adapter`, loopback bind `127.0.0.1:58083`, target
`database:3306`, and external network `ai-shopping-internal`. Port `58083` is
non-secret desired JSON configuration. It is not an active Production port:
`IMPLEMENTED=true`, `DEPLOYED=false`, and
`HOST_PORT_ACTIVE_IN_PRODUCTION=false`.

No Production access or mutation occurred, and no Production authorization was
consumed. Activation remains a separate future human-authorized WU09 mutation.
WU10 and WU11 are separate and unauthorized. The main compose, secret contract,
secret preflight, database container, external network, Governance core,
SEC-02, and `ControlledExecutionPort` were not coupled or mutated. No credential
access, MariaDB connection, or SQL execution occurred. The Mac remains the sole
Control Plane; Ubuntu has zero authority. Recovery evidence remains insufficient
and unchanged.

## Authoritative Macro-WU06 closeout reconciliation

The authoritative state is `MACRO_WU_06_CLOSE_GATE=PASS`,
`MACRO_WU_06=CLOSED`, `REMAINING_AUTHORITATIVE_MACRO_WUS=6`, and
`AUTHORITATIVE_REMAINING_RANGE=WU07-WU12`.

The factual evaluation boundary produced
`ACTUAL_OFFLINE_EVIDENCE_EVALUATION_GATE=PASS` and
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATION=EVIDENCE_INCOMPLETE`.
`AUTH_PLUGIN_EVIDENCE_STATE=MISSING`,
`PYMYSQL_COMPATIBILITY_EVIDENCE_STATE=MISSING`,
`DATA_IDENTITY_EVIDENCE_STATE=MISSING`, and
`CONTINUITY_LINEAGE_EVIDENCE_STATE=MISSING`; therefore
`RECOVER_EVIDENCE_SUFFICIENT=false` and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.

Four separately human-authorized, exact-path, metadata-only `os.lstat`
observations are filesystem I/O under existing repository terminology.
Consequently `FILESYSTEM_IO_PERFORMED=true` and
`PROTECTED_SOURCE_ACCESS_PERFORMED=true`. This does not imply content
acquisition: `FILESYSTEM_CONTENT_READ_PERFORMED=false` and
`PRODUCTION_ACCESS_PERFORMED=false`. Each repository-defined leaf was absent.
No evidence content, alternate source, fallback, enumeration, MariaDB/SQL,
PyMySQL, or secret value was accessed.

The closeout does not alter architectural authority or governance:
`MAC_CONTROL_PLANE=true`, `UBUNTU_AUTHORITY=false`,
`CONTROLLED_EXECUTION_PORT_COUPLED=false`, `GOVERNANCE_CORE_CHANGED=false`,
`SEC_02_CHANGED=false`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The current authoritative next
step is `NEXT_STEP=MACRO_WU_07_RECOVER_EVIDENCE_SUFFICIENCY_DECISION`.

## Protected Evidence Acquisition Repository Validation Closeout

`ARCHITECTURE_COMMIT=f05c652` froze the protected evidence leaf locator and
size bound before `IMPLEMENTATION_COMMIT=07bf1bd`. Repository capability and
validation state are:

```text
PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_IMPLEMENTED=true
PROTECTED_EVIDENCE_ACQUISITION_REPOSITORY_VALIDATED=true
FOCUSED_TEST_GATE=PASS
FINAL_CODE_REVIEW_GATE=PASS
CANONICAL_REGRESSION_GATE=PASS
CANONICAL_RESULT="4044 passed, 5 deselected, 555 warnings"
GIT_DIFF_CHECK_GATE=PASS
```

The boundary contains fail-closed authorization durability mechanics,
source/leaf contracts, policy, schema, codec, and tests. Durable `COMMITTED`
facts are historical facts only and provide no invocation authority. A
durability result and receipt contain no capability; Python object identity is
not authority.

```text
DURABILITY_ZERO_INVOCATION_AUTHORITY=true
DURABILITY_RESULT_NO_CAPABILITY=true
DURABILITY_RECEIPT_NO_CAPABILITY=true
PRODUCTION_HUMAN_ISSUER_AVAILABLE=false
PRODUCTION_CAPABILITY_ISSUANCE_AVAILABLE=false
PRODUCTION_ACQUISITION_AVAILABLE=false
PRODUCTION_FILESYSTEM_IO_AVAILABLE=false
```

No trusted human Production issuer is available through this repository
boundary. Both Production acquisition entry points fail closed before
filesystem I/O. This milestone performed no actual protected-source
acquisition or Production access:

```text
PROTECTED_SOURCE_ACCESS_PERFORMED=false
PRODUCTION_ACCESS_PERFORMED=false
FILESYSTEM_IO_PERFORMED=false
MAC_CONTROL_PLANE=true
UBUNTU_AUTHORITY=false
CONTROLLED_EXECUTION_PORT_COUPLED=false
GOVERNANCE_CORE_CHANGED=false
SEC_02_CHANGED=false
```

Repository validation does not promote recovery evidence or program state:

```text
RECOVER_EVIDENCE_SUFFICIENT=false
OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN
RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT
MARIADB_CONTINUITY_RECOVERY_INTEGRATED_PROGRAM=IN_PROGRESS
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```

The next operational objective is
`ACTUAL_HISTORICAL_EVIDENCE_ACQUISITION_AND_OFFLINE_EVALUATION`. It remains
subject to separate authorization and has not occurred. Existing
`datetime.utcnow` deprecations and pytest `rm_rf` cleanup warnings are
technical debt/test hygiene, not architecture blockers.

## Offline Historical Evidence Evaluator Repository Closeout

`IMPLEMENTATION_COMMIT=b51092f` completed the repository-only evaluator.
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_IMPLEMENTED=true`,
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_REPOSITORY_VALIDATED=true`,
`OFFLINE_HISTORICAL_EVIDENCE_EVALUATOR_IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`, and
`FINAL_OFFLINE_EVALUATOR_ARCHITECTURE_REVIEW_GATE=PASS`. Validation recorded
focused `14 passed in 0.03s`, `CANONICAL_REGRESSION_GATE=PASS`,
`CANONICAL_RESULT="4018 passed, 5 deselected"`, 547 warnings, and
`CANONICAL_RC=0`; `WORKTREE_AFTER_IMPLEMENTATION_PUSH=CLEAN` with
`AHEAD=0` and `BEHIND=0`.

The evaluator is repository-only, value-free, fail-closed, and has immutable,
slotted factual inputs and results. Callers cannot inject a positive result.
It freezes exactly five data identity categories—`WORDPRESS_IDENTITY`,
`SITE_IDENTITY`, `APPLICATION_IDENTITY`, `CLOSED_SCHEMA_CHARACTERISTICS`, and
`CLOSED_TABLE_CHARACTERISTICS`—and exactly three continuity lineage
categories—`LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and
`PERSISTENT_VOLUME_SNAPSHOT`. It reuses the existing
`EvidenceAcquisitionCategory`. `EVIDENCE_COMPLETE` requires provenance, but
does not promote operational `RECOVER` sufficiency.

The semantic boundary is exact:

```text
Source
!= Acquisition
!= Fact
!= OfflineEvaluation
!= RECOVERDecision
!= ProductionAccess
!= CredentialValidation
!= Authorization
!= Authority
```

The evaluator has zero mutation budget and performs no filesystem I/O,
protected-source acquisition, network activity, MariaDB/SQL connection, or
Production access. The Mac is the sole Control Plane; Ubuntu has zero
authority. Governance and SEC-02 are unchanged, and `ControlledExecutionPort`
remains uncoupled.

Operational state remains exactly:

```text
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

Actual protected evidence content must not be opened or read yet. Before any
actual acquisition, a separate architecture boundary must freeze exact
protected leaf metadata; require a regular, non-symlink leaf with permissions
no broader than `0600` and trusted UID/GID; provide stable FD/inode/device
binding and TOCTOU-resistant acquisition; bind one exact fixed source slot;
and permit one-shot, human-authorized acquisition with a maximum of one
acquisition per authorization. Enumeration, candidates, fallback, retry,
recovery, and authorization reuse are prohibited. The existing directory
metadata snapshot is point-in-time only: it is neither stable binding nor
content-acquisition authority. No trusted source contents were acquired, no
protected evidence was verified, and no Production readiness or MariaDB
credential continuity was established.

## Filesystem Target Metadata Snapshot Repository Implementation Closeout

Architecture commit `44f4ef0` preceded implementation commit `e9a3645`.
Repository validation recorded focused `122 passed in 0.09s` and canonical
`4004 passed, 5 deselected, 543 warnings`, `CANONICAL_RC=0`. Implementation Git
closeout is closed: `IMPLEMENTATION_COMMIT_RC=0`, `IMPLEMENTATION_PUSH_RC=0`,
`WORKTREE_STATE=CLEAN`, `AHEAD=0`, and `BEHIND=0`.

`FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_IMPLEMENTED=true` and
`FILESYSTEM_TARGET_METADATA_SNAPSHOT_REPOSITORY_VALIDATED=true`.
`FilesystemTargetMetadataSnapshotRequest` contains exactly `concrete_path` and
`ownership_expectation`; callers cannot supply `outcome` or
`target_classification`. `MacFilesystemTargetMetadataSnapshotAdapter` owns
filesystem observation. After complete request validation, it passes the exact
unchanged target string to at most one `os.lstat` per invocation; invalid
requests cause zero observations. Only `st_mode`, `st_uid`, and `st_gid` are
consumed.

`reason` is the sole classifier input to the repository snapshot factory. The
canonical reason-to-outcome and reason-to-classification mappings are
repository owned. The only positive vocabulary is
`DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`; `SAFE_BOUND` and
`METADATA_SAFE_AND_STABLY_BOUND` are not positive vocabulary at this boundary.
The snapshot is factual, point-in-time, and zero-authority, always preserving
`stable_handle_bound=false`, `toctou_closed=false`, and
`fd_inode_device_bound=false`. It establishes no stable binding, TOCTOU
closure, FD/inode/device binding, content acquisition, evidence admission,
evidence verification, `RECOVER` sufficiency, Production readiness, or
Production authorization.

The semantic separation remains strict:

```text
ConcreteProtectedEvidencePath
!= TrustedOwnershipExpectation
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

Operational program state remains exactly:

```text
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

Mac AIControlCenter remains the sole Control Plane. Ubuntu has zero role and
zero authority. Governance and SEC-02 remain unchanged,
`ControlledExecutionPort` remains uncoupled, and mutation budget remains zero.
Repository implementation and validation do not establish operational
filesystem I/O or authorize access to protected evidence or Production.

## Trusted Ownership Expectation Repository Implementation Closeout

Architecture freeze `c9bc387` preceded implementation `220c170`. Evidence is
focused `26 passed in 0.03s`,
`FINAL_IMPLEMENTATION_ARCHITECTURE_REVIEW_GATE=PASS`,
`CANONICAL_REGRESSION_GATE=PASS`, canonical
`3882 passed, 5 deselected, 539 warnings in 136.33s`, `CANONICAL_RC=0`, and
`IMPLEMENTATION_GIT_CLOSEOUT=CLOSED` with `WORKTREE_STATE=CLEAN`, `AHEAD=0`,
`BEHIND=0`.

`TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_IMPLEMENTED=true` and
`TRUSTED_OWNERSHIP_EXPECTATION_REPOSITORY_VALIDATED=true`. The implementation
consumes an already-existing `ResolvedTrustedMacAccountHome`, sets
`expected_uid` from `bound_uid`, performs zero additional UID observations and
zero additional passwd lookups, and uses exact repository policy
`TRUSTED_APPLICATION_GROUP_NAME="staff"`. It performs at most one
`grp.getgrnam("staff")`, uses only `gr_gid`, validates exact `int` and
non-negative GID, and fails closed with no retry, fallback, or alternate group
lookup. Immutable, slotted `TrustedOwnershipExpectation` has exactly
`expected_uid` and `expected_gid`, grants zero authority, and performs no
filesystem observation, protected-source access, or Production access.

```text
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

Mac AIControlCenter remains sole Control Plane; Ubuntu has zero role and zero
authority. Governance and SEC-02 remain unchanged, `ControlledExecutionPort`
remains uncoupled, and mutation budget remains zero. The next separately gated
repository milestone is
`MACRO_WU_06_FILESYSTEM_TARGET_METADATA_SNAPSHOT_BOUNDARY`, separate from
`TrustedOwnershipExpectation`, `ConcreteProtectedEvidencePath`, evidence
acquisition, and Production authority. It may later define
`FilesystemTargetMetadataSnapshotRequest`, `FilesystemTargetMetadataSnapshot`,
and the exact-target single-`lstat` adapter; none is implemented here.

## Trusted Ownership Expectation Architecture Contract (historical freeze)

The Macro-WU-06 prerequisite boundary was architecture-frozen in
[`docs/architecture/MACRO-WU-06-TRUSTED-OWNERSHIP-EXPECTATION-CONTRACT.md`](docs/architecture/MACRO-WU-06-TRUSTED-OWNERSHIP-EXPECTATION-CONTRACT.md).
The issuer consumes an already-existing `ResolvedTrustedMacAccountHome` and
sets `expected_uid = ResolvedTrustedMacAccountHome.bound_uid`; it performs zero
additional UID observations and zero additional passwd lookups. It neither
constructs nor executes `RuntimeHomeResolver`, and accepts no caller,
environment, `HOME`, argv, or JSON identity authority.

The exact repository-owned Mac Control Plane application-group policy is
`TRUSTED_APPLICATION_GROUP_NAME="staff"`. The issuer performs exactly one
`grp.getgrnam("staff")` lookup and uses only `gr_gid`. Lookup failure, missing
or malformed `gr_gid`, a value whose exact type is not `int`, or a negative GID
fails closed. Ambient process groups, supplementary groups, passwd `pw_gid`,
`wheel`, caller-selected values, enumeration, candidates, retries, fallbacks,
and best-effort matching are prohibited.

At architecture-freeze time, `TrustedOwnershipExpectation` was specified as a future immutable, slotted, factual,
zero-authority value with exactly `expected_uid: int` and `expected_gid: int`.
It is not unforgeable provenance, authorization, capability, admission or
verification evidence, filesystem existence/safety/metadata evidence,
`RECOVER` sufficiency, Production authorization/readiness, or a security
boundary. Possession and Python object identity grant zero authority;
downstream security-sensitive boundaries independently validate required
facts, evidence, and authority.

The dependency order is fixed:

```text
ConcreteProtectedEvidencePath + TrustedOwnershipExpectation
-> FilesystemTargetMetadataSnapshotRequest
-> at most one exact-target lstat
```

The ownership expectation must exist before a future snapshot request can make
any positive ownership comparison. That request and adapter are not implemented
here. The existing single-`lstat` contract remains `0..1` observations, with
exactly one `lstat` of the exact unchanged concrete target only after complete
request validation and no other filesystem operation. A successful directory
classification remains `DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`, never
`SAFE_BOUND` or `METADATA_SAFE_AND_STABLY_BOUND`, and preserves
`stable_handle_bound=false`, `TOCTOU_CLOSED=false`, and
`FD_INODE_DEVICE_BOUND=false`.

```text
TRUSTED_OWNERSHIP_EXPECTATION_ARCHITECTURE_FROZEN=true
TRUSTED_UID_SOURCE_ARCHITECTURE_FROZEN=true
TRUSTED_GID_SOURCE_ARCHITECTURE_FROZEN=true
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

Mac AIControlCenter remains the sole Control Plane; Ubuntu has zero role and
zero authority. Governance and SEC-02 are unchanged, `ControlledExecutionPort`
remains uncoupled, and mutation budget remains zero. After architecture Git
closeout, the separately gated next milestone is
`MACRO_WU_06_TRUSTED_OWNERSHIP_EXPECTATION_IMPLEMENTATION`; no implementation
or operational establishment is claimed by this freeze.

## Concrete Protected-Evidence Filesystem Binding Architecture Contract

The next Macro-WU-06 boundary is frozen in
[`docs/architecture/MACRO-WU-06-CONCRETE-PROTECTED-EVIDENCE-FILESYSTEM-BINDING-CONTRACT.md`](docs/architecture/MACRO-WU-06-CONCRETE-PROTECTED-EVIDENCE-FILESYSTEM-BINDING-CONTRACT.md).
Repository discovery reuses the closed fixed-slot and metadata-safety policy:
the exact protected target at this layer is a non-symlink directory, exact mode
`0700`, with structurally explicit expected UID/GID. Arbitrary caller values
are not trusted ownership authority, and no operational trusted ownership
expectation issuer or trusted GID source is implemented. The future adapter is
therefore gated from any positive operational ownership-safe claim. It performs only one
`lstat` of the exact unchanged `ConcreteProtectedEvidencePath`; it performs no
`stat`, parent walk, leaf lookup, retry, fallback, enumeration, open, or read.

`ConcreteProtectedEvidencePath` remains lexical and zero-authority. Its identity
or possession is not provenance. `TrustedOwnershipExpectation`,
`FilesystemTargetMetadataSnapshot`, existence,
inspection, safety, acquisition, admission, verification, and authority remain
strictly distinct. The snapshot-level positive concept is
`DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`, never `SAFE_BOUND` or
`METADATA_SAFE_AND_STABLY_BOUND`. A successful result is only a point-in-time
zero-authority metadata snapshot: `stable_handle_bound=false`,
`TOCTOU_CLOSED=false`, and `FD_INODE_DEVICE_BOUND=false`. Regular
file/`0600`, FD/inode/device binding, and content acquisition remain later
separate boundaries. Mutation budget is zero; Governance/SEC-02 are unchanged;
`ControlledExecutionPort` remains uncoupled. This architecture work performed
no filesystem I/O, protected-source access, Production access, or runtime path
establishment, and Macro-WU-06 accounting remains unchanged.

## Concrete Protected-Evidence Path Composer Repository Implementation Closeout

The repository-only composer is implemented and validated:
`CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_IMPLEMENTED=true` and
`CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSER_REPOSITORY_VALIDATED=true`.
Architecture contract commit `254241a` preceded implementation commit `2810c0c`.
Validation evidence is focused `11 passed in 0.03s`,
`FINAL_ARCHITECTURE_REVIEW_GATE=PASS`, and
`CANONICAL_REGRESSION_GATE=PASS`, with
`CANONICAL_RESULT=3856 passed, 5 deselected, 535 warnings in 133.68s (0:02:13)`
and `CANONICAL_RC=0`. Git evidence is
`IMPLEMENTATION_GIT_CLOSEOUT=CLOSED`, `WORKTREE_STATE=CLEAN`, `AHEAD=0`, and
`BEHIND=0`.

`ConcreteProtectedEvidencePath` is lexical only and has zero authority. It is
not provenance, authorization, capability, verification evidence, filesystem
existence or safety evidence, `RECOVER` evidence sufficiency, Production
authorization/readiness, or a security boundary. Python object identity is not
a security boundary. Downstream security-sensitive boundaries independently
validate the facts, evidence, and authority they require.

This repository capability establishes no runtime path or external fact:

```text
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

Mac AIControlCenter remains the sole Control Plane. Ubuntu has zero role and
zero authority. Governance and SEC-02 are unchanged, and
`ControlledExecutionPort` remains uncoupled.

## Concrete Protected-Evidence Path Composition Architecture Contract

The architecture contract for the next distinct Macro-WU06 boundary is frozen
in
[`docs/architecture/MACRO-WU-06-CONCRETE-PROTECTED-EVIDENCE-PATH-COMPOSITION-CONTRACT.md`](docs/architecture/MACRO-WU-06-CONCRETE-PROTECTED-EVIDENCE-PATH-COMPOSITION-CONTRACT.md).
Repository discovery confirmed the authoritative inputs already exist as
`ResolvedTrustedMacAccountHome` and `RuntimeHomeResolver` in the trusted-home
runtime resolver module, and `AuthoritativeMacProtectedEvidenceSuffixPolicy`,
`AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity`, and
`EXACT_PROTECTED_EVIDENCE_SUFFIX` in the suffix-policy module. Existing source,
profile, fixed-slot, and concrete-source-location contracts remain separate and
do not define this lexical composition boundary.

The future composer consumes an already-existing
`ResolvedTrustedMacAccountHome`; it must not execute `RuntimeHomeResolver` or
observe platform, UID, effective UID, or passwd state. It accepts no caller,
environment, argv, alternate, candidate, fallback, or enumerated suffix or
path. It uses only the repository-owned exact suffix
`Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`.

Composition is deterministic string-only composition: if `passwd_home` ends
with `/`, append the suffix directly; otherwise append `/` and then the suffix.
This inserts at most one boundary separator and otherwise preserves both input
strings unchanged. No path library, expansion, joining, stripping,
normalization, absolutization, resolution, realpath, or canonicalization is
permitted, and no filesystem observation of any kind occurs.

`ConcreteProtectedEvidencePath` is frozen as an immutable, slotted,
zero-authority value concept with exactly one data field, `concrete_path`. It is
not unforgeable provenance, authorization, capability, admission or
verification evidence, `RECOVER` sufficiency, filesystem evidence, Production
authorization/readiness, or a security boundary. Possession and Python object
identity grant no authority; later security-sensitive boundaries independently
validate every fact, item of evidence, and authority they require.

This architecture work composes no runtime value. Mac AIControlCenter remains
the sole Control Plane; Ubuntu has no role and zero authority. Governance and
SEC-02 are unchanged, `ControlledExecutionPort` remains uncoupled, and no
execution or mutation authority is granted. Preserved state is:

```text
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

Historically, after Git closeout of this contract, the next local submilestone was
`MACRO_WU_06_CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSITION_IMPLEMENTATION`, a
repository-only, zero-authority implementation with no protected-source or
Production access. That implementation is complete under architecture commit
`254241a`, implementation commit `2810c0c`, and documentation closeout commit
`94c36fb`. The current next repository boundary is
`MACRO_WU_06_CONCRETE_PROTECTED_EVIDENCE_FILESYSTEM_BINDING`.

## Trusted Mac Account-Home Runtime Resolver Implementation — Documentation Closeout

The repository implementation exists and is repository-validated; this is not
a claim of runtime resolver invocation:
`RUNTIME_HOME_RESOLVER_REPOSITORY_IMPLEMENTED=true` and
`RUNTIME_HOME_RESOLVER_REPOSITORY_VALIDATED=true`. Chronology is fixed by
architecture contract commit `41963c1`, architecture clarification commit
`cf9c34d`, and implementation commit `288eb68`. Focused validation was
`28 passed in 0.03s`; Final Architecture Review was `PASS`; canonical validation
was `3845 passed, 5 deselected, 531 warnings` with `CANONICAL_RC=0`.

`RuntimeHomeResolver` observes `platform.system()` exactly once, requires exact
`Darwin`, and fails before UID observation on platform failure. It then observes
`os.getuid()` exactly once and `os.geteuid()` exactly once, completing both UID
observations before root validation; it rejects either UID equal to zero,
requires equality, binds that equal UID, and calls `pwd.getpwuid(bound_uid)`
exactly once. The returned `pw_dir` must have exact `str` type (rejecting `str`
subclasses), be non-empty and NUL-free, and be a lexically absolute POSIX
string. The passwd-derived string is preserved unchanged.

The resolver fails closed with no retry, fallback, reconnect, recovery,
`getpwnam`, `HOME`/environment/argv/caller home authority, `Path.home`,
`expanduser`, `strip`, normalization, resolve/realpath/canonicalization,
`stat`/`lstat`/`exists`/`is_dir`/`is_symlink`, filesystem probing,
ownership/mode inspection, or path enumeration.

`ResolvedTrustedMacAccountHome` is immutable and slotted with exactly two data
fields, `bound_uid` and `passwd_home`. Normal/direct supported construction is
prohibited; successful `RuntimeHomeResolver` resolution is the supported
creation path, and there is no public convenience factory accepting arbitrary
UID/home values. It has zero authority and is not an unforgeable provenance
token, authorization, capability, admission or verification evidence,
`RECOVER` evidence sufficiency, Production authorization/readiness, or a
security boundary. Possession or identity grants zero authority; downstream
security-sensitive boundaries independently validate their evidence and
authority.

Semantic separation remains exact: `TrustedMacAccountHomePolicy` !=
`RuntimeAccountIdentityObservation` != `RuntimeHomeResolver` !=
`ResolvedTrustedMacAccountHome` !=
`AuthoritativeMacProtectedEvidenceSuffixPolicy` != `ProtectedEvidenceSuffix` !=
`ConcreteProtectedEvidencePath` != `SourceExistence` != `MetadataInspection` !=
`MetadataSafety` != `ContentAcquisition` != `Admission` != `Verification` !=
`Authority`. Mac AIControlCenter remains sole Control Plane; Ubuntu has zero
resolver authority. Governance and SEC-02 are unchanged, and
`ControlledExecutionPort` remains uncoupled.

Repository implementation availability does not claim that this documentation
work executed the resolver or established a trusted home or concrete path:

```text
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
MACRO_WU_06_TRUSTED_MAC_ACCOUNT_HOME_RUNTIME_RESOLVER_IMPLEMENTATION=CLOSED
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```

Actual historical evidence acquisition and offline evaluation are still
required before Macro-WU06 can close. Next is read-only architecture
discovery/freeze for composing `ResolvedTrustedMacAccountHome` with the already
frozen exact protected-evidence suffix into a distinct, zero-authority
`ConcreteProtectedEvidencePath`; that work must not inspect existence or
metadata, perform `stat`/`lstat`, access or acquire protected evidence, grant
authority, or access Production.

## Trusted Mac Account-Home Runtime Resolver Architecture Contract

The future runtime resolver boundary is frozen in
[`docs/architecture/MACRO-WU-06-TRUSTED-MAC-ACCOUNT-HOME-RUNTIME-RESOLVER-CONTRACT.md`](docs/architecture/MACRO-WU-06-TRUSTED-MAC-ACCOUNT-HOME-RUNTIME-RESOLVER-CONTRACT.md).
It requires exactly one `platform.system()` observation and the exact returned
value `Darwin` before UID observation, one real-UID observation, one
effective-UID observation, non-root equal UIDs, and exactly one
`pwd.getpwuid(bound_uid)` lookup. Every failure is fail-closed; no retry,
fallback, alternate account lookup, caller/environment/argv input, or recovery
semantics exist.

The passwd `pw_dir` must exist as a result field and be a non-empty, NUL-free
string that is lexically absolute as a POSIX path. It is preserved unchanged:
no stripping, expansion, normalization, resolution, canonicalization, metadata
inspection, existence/directory check, enumeration, or filesystem probe is
allowed. `ResolvedTrustedMacAccountHome` is an immutable zero-authority output
concept, slotted with exactly the `bound_uid` and `passwd_home` data fields.
Normal or direct supported construction is prohibited; successful
`RuntimeHomeResolver` construction is the supported path. Python object-model
mechanisms can theoretically bypass normal construction, so the object is not
an unforgeable provenance token, authorization or admission token, capability,
verification evidence, `RECOVER` evidence sufficiency, Production
authorization/readiness, or a security boundary. Possession or identity grants
zero authority, and every later security-sensitive boundary must independently
validate its required evidence and authority.

This is architecture only: `RUNTIME_HOME_RESOLVER_AVAILABLE=false`, no trusted
home or concrete path is established, and no filesystem, protected-source, or
Production access occurred. Policy, observation, resolver, resolved value,
suffix policy/value, concrete path, existence, inspection, safety, acquisition,
admission, verification, and authority remain distinct. Mac AIControlCenter
remains sole Control Plane; Ubuntu has no resolver role and zero authority.
Governance and SEC-02 are unchanged, `ControlledExecutionPort` is not coupled,
and the preserved Macro-WU06 state remains in progress with seven authoritative
WUs remaining across WU06-WU12.

## Trusted Mac Account-Home Repository Policy Implementation — Documentation Closeout

Chronology is fixed: the architecture contract/freeze was committed first at
`d9def864c83e3660ce9e6afa646ee4f5851934b3`; the symbolic, zero-authority
repository policy implementation was then completed and Git-closed at
`d07054901b5c3eccac401e90afa4126a9bda9515`.

The implemented policy is Darwin-only, rejects the root account, takes the real
UID from `os.getuid()` and the effective UID from `os.geteuid()`, requires those
UIDs to be equal, and freezes the future account-home lookup rule as
`pwd.getpwuid(bound_uid).pw_dir`. It does not execute runtime UID or passwd
lookup and does not implement a runtime home resolver.

It establishes no trusted home value, absolute path, concrete protected
evidence path, filesystem I/O, protected-source or Production access, evidence
acquisition, admission, verification, authorization, capability, execution, or
mutation authority. No protected evidence directory is asserted to exist and
no filesystem metadata was inspected.

Architecture separation remains exact: trusted Mac account-home policy !=
runtime account identity observation != runtime home resolver != resolved
trusted home value != protected evidence suffix != absolute path composition !=
source existence != metadata inspection != metadata safety != content
acquisition != admission != verification != authority.

Current facts remain:

```text
RUNTIME_HOME_RESOLVER_AVAILABLE=false
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

Validation evidence was focused `6 passed in 0.06s`, Final Architecture Review
`PASS`, and canonical `3817 passed, 5 deselected, 527 warnings in 133.93s` with
`CANONICAL_RC=0`. Implementation Git closeout passed with `COMMIT_RC=0`,
`PUSH_RC=0`, a clean final worktree, `AHEAD=0`, and `BEHIND=0`.

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
infrastructure worker with zero authority. Production validation is not ready
and Shopping runtime is not activated. After this documentation closeout, the
next repository activity is read-only architecture discovery/freeze for the
runtime trusted Mac account-home resolver boundary; that resolver is not yet
implemented. The next Production-relevant milestone remains Macro-WU06 Actual
Historical Evidence Acquisition + Offline Evaluation.

## Trusted Mac Account-Home Policy Architecture Contract

The trusted account-home boundary for future protected external evidence path
composition is frozen in
[`docs/architecture/MACRO-WU-06-TRUSTED-MAC-ACCOUNT-HOME-POLICY-CONTRACT.md`](docs/architecture/MACRO-WU-06-TRUSTED-MAC-ACCOUNT-HOME-POLICY-CONTRACT.md).
The platform must be Darwin; root is rejected. `os.getuid()` supplies the real
UID and `os.geteuid()` supplies the effective UID. They must be equal, and the
single bound UID is the account identity. The future lookup rule is
`pwd.getpwuid(bound_uid).pw_dir`; this work neither executes it nor implements a
runtime resolver.

`HOME`, `Path.home`, `expanduser`, caller-selected home/path, argv home/path,
fallback, enumeration, and candidate iteration are rejected as authority.
Existing Governance paths, operational bootstrap resolution, Shopping
`control_plane_home`, and runtime home conventions remain non-authoritative
design evidence only. The exact suffix remains relative and uncomposed. No
trusted home, absolute/concrete path, filesystem I/O, source access, metadata
fact, acquisition, admission, verification, or authority is established.

Mac AIControlCenter remains sole Control Plane; Ubuntu remains stateless with
zero authority. Governance and SEC-02 remain separate and unchanged, and
`ControlledExecutionPort` is not coupled. `RECOVER_EVIDENCE_GATE` remains
`RECOVER_EVIDENCE_INSUFFICIENT`; `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## Authoritative Mac Protected Evidence Suffix Policy Implementation — Documentation Closeout

The exact suffix architecture contract was established first at commit
`e1e66ac17b3506a4bff4bd0a9322fc7360ca6536`. The repository-only suffix policy
implementation then closed at commit `6c7b18ab942024120b06d1eb0235c7b67b7916df`
as `MACRO_WU_06_AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY_IMPLEMENTATION`.
That repository implementation submilestone is closed; Macro-WU06 is not closed.

The implementation owns the exact relative suffix
`Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`.
`EXACT_SUFFIX_POLICY_LAYER_REQUIRED=true`,
`EXACT_SUFFIX_POLICY_EVIDENCE=ESTABLISHED_BY_ARCHITECTURE_DECISION`,
`EXACT_SUFFIX_VALUE_ESTABLISHED=true`, and
`SUFFIX_IS_RELATIVE_TO_TRUSTED_ACCOUNT_HOME=true`.

Architecture separation remains exact:
`ProtectedExternalEvidenceBaseLocationIdentity` !=
`AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity` !=
`AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity` != exact suffix value
!= runtime trusted Mac account-home resolution != absolute path != concrete path
!= source existence != metadata inspection != metadata safety != content
acquisition != admission != verification != authority. There is no caller
path/base/home/suffix authority, environment or `HOME` authority, argv authority,
fallback, enumeration, candidate iteration, filesystem I/O, protected-source or
Production access, MariaDB connection, SQL, PyMySQL execution, Docker/Colima
mutation, Ubuntu authority, Governance-core coupling, SEC-02 semantic change, or
`ControlledExecutionPort` coupling. The legacy caller-path observer remains
isolated and unreachable.

`ABSOLUTE_PATH_ESTABLISHED=false`, `CONCRETE_PATH_VALUE_ESTABLISHED=false`,
`RUNTIME_HOME_RESOLVER_AVAILABLE=false`,
`AUTHORITATIVE_BASE_LOCATION_ALREADY_EXISTS=false`,
`SOURCE_EXISTENCE_ESTABLISHED=false`,
`HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false`,
`METADATA_INSPECTION_PERFORMED=false`, `SOURCE_METADATA_SAFE=false`,
`CONTENT_ACQUISITION_PERFORMED=false`, `EVIDENCE_ADMITTED=false`,
`EVIDENCE_VERIFIED=false`, `RECOVER_EVIDENCE_SUFFICIENT=false`,
`PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, and
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

Focused validation was `6 passed in 0.06s`; Final Architecture Review was
`PASS`; canonical validation was `3811 passed, 5 deselected, 523 warnings in
134.83s` with `CANONICAL_RC=0`. Warnings were non-failing. Mac AIControlCenter
remains the sole Control Plane; Ubuntu remains a stateless infrastructure worker
with zero Control Plane authority. `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

The next repository activity is architecture discovery/freeze of the trusted
Mac account-home resolution boundary before any concrete path composition or
runtime resolver. The next Production-relevant milestone remains actual
historical evidence acquisition and offline evaluation completion under
Macro-WU06.

## Protected External Evidence Exact Suffix Architecture Contract

The repository-owned exact suffix is established by architecture decision as
`Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`.
It is relative to a future trusted Mac account-home resolver; it is not an
absolute or concrete path, and no runtime home resolver exists. The complete
contract is
[`docs/architecture/MACRO-WU-06-PROTECTED-EXTERNAL-EVIDENCE-SUFFIX-CONTRACT.md`](docs/architecture/MACRO-WU-06-PROTECTED-EXTERNAL-EVIDENCE-SUFFIX-CONTRACT.md).

The repository layer is
`AuthoritativeMacProtectedEvidenceSuffixPolicy`, with identity
`AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity` and symbolic identity
`AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY`; it was subsequently
implemented at commit `6c7b18ab942024120b06d1eb0235c7b67b7916df`. Exact suffix
policy remains distinct from base
location identity, base-path policy identity, runtime account-home resolution,
concrete path, existence, inspection, safety, acquisition, admission,
verification, and authority. Existing governance, shopping-secret,
runtime/build/staging, WordPress/WooCommerce, and Ubuntu paths acquire no
authority.

All caller base-path/path/suffix injection, environment or HOME authority, argv
authority, fallback, enumeration, and candidate iteration remain prohibited.
The contract grants zero authority. Mac AIControlCenter remains the sole Control
Plane; Ubuntu remains a stateless zero-authority infrastructure worker.
Governance and SEC-02 semantics are unchanged, and `ControlledExecutionPort` is
not coupled.

`EXACT_SUFFIX_POLICY_LAYER_REQUIRED=true`,
`EXACT_SUFFIX_POLICY_EVIDENCE=ESTABLISHED_BY_ARCHITECTURE_DECISION`,
`EXACT_SUFFIX_VALUE_ESTABLISHED=true`, and
`SUFFIX_IS_RELATIVE_TO_TRUSTED_ACCOUNT_HOME=true`. Absolute/concrete path,
resolver availability, existence, inspection, safety, acquisition, admission,
verification, and Production readiness remain false or unestablished.
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12` remain authoritative. The contract did
not itself authorize implementation; the later implementation closeout is
recorded above.

## Authoritative Mac Base Path Policy Implementation — Documentation Closeout

`MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION` is `CLOSED` as a
repository-only implementation/documentation submilestone. Macro-WU06 is not
complete. Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a
stateless zero-authority infrastructure worker.

`AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity` is symbolic policy
identity only. `AuthoritativeMacProtectedEvidenceBasePathPolicy` is
repository-owned and value-free. Its mapping from
`ProtectedExternalEvidenceBaseLocationIdentity` is immutable and closed. The
canonical factory accepts no caller path, home, or suffix input. No runtime
account-home resolver exists. Production/source implementation uses none of
`Path.home`, `HOME`, `os.environ`, `os.getenv`, `sys.argv`, `pwd.getpwuid`,
`os.getuid`, or `os.getgid`.

There is zero filesystem I/O and no filesystem adapter, metadata inspector,
content reader, or Production adapter. The policy has zero authorization,
capability, execution, mutation, retry, reconnect, rollback, acquisition,
admission, or verification authority. Governance core semantics did not change;
SEC-02 was neither reused nor changed; there is no `ControlledExecutionPort`
coupling.

Architecture separation is exact: repository policy identity != exact suffix
policy != runtime account-home resolution != concrete path != source existence
!= metadata inspection != metadata safety != content acquisition != admission
!= verification != authority. The exact protected-evidence suffix was unresolved
within that earlier implementation submilestone; the subsequent architecture
decision above now establishes it. No directory, concrete path, source
existence, metadata inspection, or Production access is established or implied.

Implementation commit `ab9de4a08c35de3805983346cf7f1a6d9accccdb` was pushed
successfully with `AHEAD=0` and `BEHIND=0`. Focused validation was `6 passed in
0.05s`; final architecture review was `PASS`; canonical validation was `3805
passed, 5 deselected, 519 warnings` with `CANONICAL_RC=0`. The warnings were
non-failing.

Preserved state:

```text
BASE_PATH_POLICY_LAYER_REQUIRED=true
AUTHORITATIVE_BASE_PATH_POLICY_DEFINED=true
AUTHORITATIVE_BASE_LOCATION_ALREADY_EXISTS=false
EXACT_PROTECTED_EVIDENCE_SUFFIX_ESTABLISHED=false
CONCRETE_PATH_VALUE_ESTABLISHED=false
SOURCE_EXISTENCE_ESTABLISHED=false
HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false
METADATA_INSPECTION_PERFORMED=false
SOURCE_METADATA_SAFE=false
CONTENT_ACQUISITION_PERFORMED=false
EVIDENCE_ADMITTED=false
EVIDENCE_VERIFIED=false
RECOVER_EVIDENCE_SUFFICIENT=false
OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN
PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false
PRODUCTION_VALIDATION_READY=false
SHOPPING_RUNTIME_ACTIVATED=false
RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT
SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```

The subsequent repository architecture contract now establishes the exact
relative suffix, without establishing an absolute/concrete path or runtime
resolver, as recorded above.

## Protected External Evidence Source Access and Metadata Inspection Boundary — Documentation Closeout

`MACRO_WU_06_PROTECTED_EXTERNAL_EVIDENCE_SOURCE_ACCESS_AND_METADATA_INSPECTION_BOUNDARY`
is `CLOSED` as a repository implementation submilestone only; Macro-WU-06 is not
closed. Mac AIControlCenter remains the sole Control Plane, and Ubuntu remains a
stateless infrastructure worker with zero authority here.

The metadata boundary is repository-owned, path-free, and zero-authority.
`ProtectedSourceMetadataInspectionRequest` carries only the closed symbolic
source identity with `mutation_budget=0`. Capability binding uses exact
request-instance identity, not dataclass structural equality.
Same-source/different-request and cross-source substitutions are rejected before
consumption; a mismatched request does not consume the capability; the original exact request
succeeds at most once; subsequent reuse is rejected; and concurrent consumption
remains exactly once.

Inert test classification provenance is explicitly distinct from operational
factual evidence, and inert `SAFE_BOUND` is not operational evidence. No
supported `HUMAN_AUTHORIZED_OPERATIONAL_INSPECTION` evidence issuer exists.
`OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED=false`,
`OPERATIONAL_CANONICAL_PATH_ISSUER_IMPLEMENTED=false`, and
`PRODUCTION_OPERATIONAL_INSPECTION_AVAILABLE=false`. Legacy
`observe_fixed_protected_source` remains isolated and is not reachable through
the new boundary. No caller path, callback, HOME/environment, argv, fallback,
enumeration, or candidate-iteration authority exists. Governance/SEC-02
semantics are unchanged, and `ControlledExecutionPort` is not reused.

Focused validation was exactly `27 passed`; final architecture review was
`PASS`; canonical was exactly `3799 passed, 5 deselected, 515 warnings` with
`CANONICAL_RC=0`. Warnings were not failures. Implementation commit
`daff799d35709da31434ebb280e0771073b12b52` was pushed successfully. Production
access, protected-source access, metadata inspection, and content acquisition
were not performed. No MariaDB, SQL, PyMySQL, Docker, Colima, or Ubuntu activity
occurred.

The completed architecture discovery/freeze records
`BASE_PATH_POLICY_LAYER_REQUIRED=YES`, with proposed layer
`AuthoritativeMacProtectedEvidenceBasePathPolicy` and proposed identity model
`AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity`. Existing
`ProtectedExternalEvidenceBaseLocationIdentity.PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION`
is symbolic input only and does not establish a filesystem path. Repository-owned
base-path policy != runtime account-home resolution != concrete path != source
existence != metadata inspection != metadata safety. A future Mac runtime resolver
may use trusted OS account identity semantics such as
`pwd.getpwuid(os.getuid()).pw_dir`, but only after exact repository-owned path
suffix policy is established. No authoritative exact filesystem suffix or path
has been selected.

Frozen state is `CONCRETE_PATH_VALUE_ESTABLISHED=false`,
`AUTHORITATIVE_BASE_LOCATION_ALREADY_EXISTS=false`,
`SOURCE_EXISTENCE_ESTABLISHED=false`,
`HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false`,
`METADATA_INSPECTION_PERFORMED=false`, `SOURCE_METADATA_SAFE=false`,
`CONTENT_ACQUISITION_PERFORMED=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
and `PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`. Also frozen are
`CALLER_BASE_PATH_SELECTION_ALLOWED=false`, `CALLER_PATH_INJECTION_ALLOWED=false`,
`ENVIRONMENT_PATH_AUTHORITY_ALLOWED=false`, `HOME_ENVIRONMENT_AUTHORITY_ALLOWED=false`,
`FALLBACK_ALLOWED=false`, `PATH_ENUMERATION_ALLOWED=false`, and
`CANDIDATE_ITERATION_ALLOWED=false`.

`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
Actual historical evidence acquisition and offline evaluation have not occurred,
so `MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12` remain authoritative.

At this earlier boundary closeout, the next repository-only submilestone was
`MACRO_WU_06_AUTHORITATIVE_MAC_BASE_PATH_POLICY_IMPLEMENTATION`. It is now
closed as recorded above and remains value-free, with zero filesystem I/O, zero
Production access, no concrete path resolution, source-existence check, metadata
inspection, runtime resolver, or protected-source access. The exact
protected-evidence suffix remains unresolved and must not be guessed.

## Protected External Evidence Concrete Source Location Descriptor — Documentation Closeout

Exactly four closed symbolic `ProtectedExternalEvidenceConcreteSourceLocationIdentity`
values map one-to-one and immutably from the four
`ProtectedExternalEvidenceFixedSourceSlotIdentity` values. This layer establishes
only a Concrete Source Location Descriptor. It establishes no Authoritative Mac
Base Path, Concrete Path Value, Source Existence, Historical Evidence Existence,
Metadata Inspection, Metadata Safety, Content Acquisition, Admission,
Verification, `RECOVER` Evidence Sufficiency, or Authority.

Semantic separation is exact: `EvidenceAcquisitionCategory` != Source Bundle
Identity != Protected Source Profile Identity != Fixed Source Slot Identity !=
Concrete Source Location Descriptor != Concrete Path Value != Source Existence
!= Metadata Inspection != Metadata Safety != Content Acquisition != Admission
!= Verification != Authority. `PROTECTED_EXTERNAL_EVIDENCE_BASE_LOCATION` is a
closed repository policy identity only—not a filesystem path, directory
existence fact, resolved path, metadata-safe location, or acquisition source.

Current facts are `AUTHORITATIVE_BASE_LOCATION_ALREADY_EXISTS=false`,
`CONCRETE_PATH_VALUE_ESTABLISHED=false`, `SOURCE_EXISTENCE_ESTABLISHED=false`,
`HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false`,
`METADATA_INSPECTION_PERFORMED=false`, `SOURCE_METADATA_SAFE=false`,
`CONTENT_ACQUISITION_PERFORMED=false`, `OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN`,
and `PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`. Location/path authority is
closed: caller location selection and path injection, environment/HOME/argv
authority, fallback, path enumeration, and candidate iteration are all false.

Internal reverse lookup is deterministic traversal of a closed immutable
repository mapping solely to recover canonical profile identity. It is not
filesystem or path discovery, candidate iteration, fallback, probing, caller
selection, or environment authority.

Descriptors reuse canonical Fixed Source Slot protection requirements without
claiming operational satisfaction: Mac Control Plane ownership outside Git;
protected parent exact `0700`; regular non-symlink leaf no broader than `0600`;
explicit trusted uid/gid; future FD/inode binding, explicit human authorization,
and one-shot acquisition; maximum one acquisition per future authorization; no
fallback, enumeration, candidate iteration, environment/HOME authority, argv or
JSON secret-value transport, secret logging, or secret hashing.

Chronology: focused `7 passed in 0.06s`; authoritative final architecture review
`PASS`; canonical exactly once, `3772 passed, 5 deselected, 511 warnings in
134.12s (0:02:14)`, `CANONICAL_RC=0`; no code/test correction and no canonical
rerun; implementation Git closeout
`CONCRETE_SOURCE_LOCATION_IMPLEMENTATION_GIT_CLOSEOUT=PASS` at
`c3760d2fd9bb0810d3e285ec203b40e5b7b77814`, `AHEAD=0`, `BEHIND=0`.

No Governance or `ControlledExecutionPort` behavior changed. No authorization,
mutation-budget, SEC-02, durable-consumption, SQLite-governance, capability,
retry, rollback, or Production-mutation semantics changed. Preserved governance
is `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, `ROTATE_AUTHORIZED=false`,
`REPLACE_AUTHORIZED=false`, `STRATEGY_EXECUTED=false`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
The exact six Shopping secret actions remain unchanged and
`SHOPPING_SECRET_PROVISIONING` remains target-only.

Mac AIControlCenter remains sole Control Plane; Ubuntu remains a stateless
infrastructure worker with zero Control Plane authority. This is repository
preparation inside Macro-WU-06 Actual Historical Evidence Acquisition + Offline
Evaluation. Neither activity occurred; `RECOVER_EVIDENCE_SUFFICIENT` has not
been factually evaluated, and Macro-WU-07 has not started.
`MACRO_WU_06=IN_PROGRESS`, `REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`.

## Protected External Evidence Fixed Source Slot — Documentation Closeout

This repository-preparation submilestone belongs inside authoritative Macro-WU-06
Actual Historical Evidence Acquisition + Offline Evaluation; it is not
authoritative Macro-WU-07. `MACRO_WU_06=IN_PROGRESS`,
`REMAINING_AUTHORITATIVE_MACRO_WUS=7`, and
`AUTHORITATIVE_REMAINING_RANGE=WU06-WU12`. Original authoritative Macro-WU-07
remains the later factual `RECOVER_EVIDENCE_SUFFICIENT` decision. This contract
completed neither actual historical evidence acquisition nor offline evidence
evaluation, and does not close Macro-WU-06.

The exact four-file implementation established exactly four symbolic
`ProtectedExternalEvidenceFixedSourceSlotIdentity` values:
`AUTH_PLUGIN_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`,
`PYMYSQL_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`,
`DATA_IDENTITY_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`, and
`CONTINUITY_LINEAGE_PROTECTED_EVIDENCE_FIXED_SOURCE_SLOT`. The repository owns
an immutable one-to-one mapping from
`ProtectedExternalEvidenceSourceProfileIdentity` to
`ProtectedExternalEvidenceFixedSourceSlotIdentity`.
`CALLER_SLOT_SELECTION_ALLOWED=false` and `CALLER_PATH_INJECTION_ALLOWED=false`.

Architecture separation is exact: `EvidenceAcquisitionCategory` != Source Bundle
Identity != Protected Source Profile Identity != Fixed Source Slot Identity !=
Concrete Source Location != Source Existence != Metadata Safety != Content
Acquisition != Admission != Verification != Authority. Fixed Source Slot Identity
is symbolic only and is not any downstream fact in that chain.
`CATEGORY_TO_BUNDLE_MAPPING_IS_VERIFICATION_REQUIREMENT_SCOPE=false`.

Chronology: exact four-file implementation -> focused `40 passed in 0.14s` ->
authoritative final architecture review `PASS` -> canonical exactly once ->
`3765 passed, 5 deselected, 507 warnings in 134.47s` with `CANONICAL_RC=0` -> no
code/test correction -> no canonical rerun -> implementation commit
`7ccebffcce281590d57f4f8fc93d9e53032bb822` -> implementation push `PASS` ->
`AHEAD=0` and `BEHIND=0`. `IMPLEMENTATION_GIT_CLOSEOUT=PASS` and `GIT_PUSH=PASS`.

Current facts remain fail-closed: `CONCRETE_PATH_ESTABLISHED=false`,
`SOURCE_EXISTENCE_ESTABLISHED=false`,
`HISTORICAL_EVIDENCE_EXISTENCE_ESTABLISHED=false`,
`METADATA_INSPECTION_PERFORMED=false`, `SOURCE_METADATA_SAFE=false`,
`CONTENT_ACQUISITION_PERFORMED=false`.
`OFFLINE_ACQUISITION_POSSIBLE=UNKNOWN` and
`PRODUCTION_ACCESS_CURRENTLY_JUSTIFIED=false`. Actual historical evidence
acquisition and offline evaluation have not occurred; historical evidence
existence, a concrete source location, and source metadata safety are not
established, and `RECOVER_EVIDENCE_SUFFICIENT` has not been factually evaluated.
Therefore authoritative Macro-WU-06 remains `IN_PROGRESS`.

Protection requirements are future policy only, not operationally satisfied.
They require Mac Control Plane ownership outside Git; a protected parent at
exact mode `0700`; a regular non-symlink leaf with permissions no broader than
`0600`; an explicit trusted uid/gid; future FD/inode binding, explicit human
authorization, and one-shot acquisition; maximum one acquisition per future
authorization; and no fallback, enumeration, candidate iteration,
environment/HOME authority, argv secret transport, JSON secret-value transport,
secret logging, or secret hashing.

Preserved governance is `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`, `ROTATE_AUTHORIZED=false`,
`REPLACE_AUTHORIZED=false`, `STRATEGY_EXECUTED=false`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
The exact six Shopping actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only. Operational truth is
`PRODUCTION_ACCESS=NOT_PERFORMED`, `MARIADB_ACTIVITY=NONE`,
`SECRET_VALUES_READ=NO`, `METADATA_INSPECTION=NOT_PERFORMED`,
`CONTENT_ACQUISITION=NOT_PERFORMED`, `SQL_EXECUTION=NOT_PERFORMED`,
`PYMYSQL_ACTIVITY=NONE`, and `NOTION_SYNC=NOT_PERFORMED`.

No Governance, `ControlledExecutionPort`, or authorization behavior changed.

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
infrastructure worker and has no Control Plane authority.

## MariaDB Continuity Integrated WU-09 — Evidence Acquisition Descriptor Documentation Closeout

Exact closeout chronology: `MARIADB_CONTINUITY_INTEGRATED_WU_07_DISCOVERY_RECONCILE_GATE=PASS`,
`MARIADB_CONTINUITY_INTEGRATED_WU_07_IMPLEMENTATION_GATE=PASS`,
`MARIADB_CONTINUITY_INTEGRATED_WU_07_FOCUSED_GATE=PASS`,
`FOCUSED_RESULT=17 passed in 0.07s`,
`MARIADB_CONTINUITY_INTEGRATED_WU_07_FINAL_ARCHITECTURE_REVIEW_GATE=PASS`,
`MARIADB_CONTINUITY_INTEGRATED_WU_08_CANONICAL_GATE=PASS`,
`CANONICAL_RESULT=3733 passed, 5 deselected, 495 warnings`, `CANONICAL_RC=0`,
`IMPLEMENTATION_GIT_CLOSEOUT=PASS`,
`IMPLEMENTATION_COMMIT=63370cfdf4ea0c80ca54395dd5913317ba529dca`, `GIT_PUSH=PASS`,
`AHEAD=0`, and `BEHIND=0`.

The exact four-file implementation defines a closed, repository-only and
value-free Evidence Acquisition Descriptor Contract with twelve classifications:
auth-plugin authoritative evidence, PyMySQL 1.2.0 compatibility evidence,
expected database identity, expected account identity, required grants,
five-category data identity, three-category continuity lineage, timestamp
evidence, immutable integrity binding, trusted issuer, account binding, and
baseline binding. Classification is not source identity, and neither implies
source existence, acquisition, evidence existence, admission, verification,
authoritative evidence, provenance, integrity, timestamp, issuer,
account/baseline binding, identity completeness, continuity completeness,
`RECOVER` sufficiency, Production readiness, or authority.

The contract does not locate, retrieve, ingest, parse, admit, or verify evidence.
It establishes no source or evidence existence and no authoritative evidence,
verified provenance, integrity/timestamp/trusted-issuer binding, expected
database/account/grants binding, identity completeness, or continuity lineage
completeness. Caller positive-fact, source-path, arbitrary-reference, external
evidence-value, and secret-bearing-content injection remain prohibited. It is
fail-closed and has zero acquisition, admission, or verification authority,
with zero I/O, network, SQL, Production access, or runtime mutation.

Mac AIControlCenter remains sole Control Plane; Ubuntu remains a stateless
infrastructure worker. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact
six Shopping actions remain unchanged; `SHOPPING_SECRET_PROVISIONING` remains
target-only; `RECOVER` evidence remains insufficient;
`ROTATE_AUTHORIZED=false`; `REPLACE_AUTHORIZED=false`;
`STRATEGY_EXECUTED=false`; `PRODUCTION_VALIDATION_READY=false`; and
`SHOPPING_RUNTIME_ACTIVATED=false`. Operational truth is
`PRODUCTION_ACCESS=NOT_PERFORMED`, `MARIADB_ACTIVITY=NONE`,
`SECRET_VALUES_READ=NO`, `SQL_EXECUTION=NOT_PERFORMED`,
`PYMYSQL_ACTIVITY=NONE`, and `NOTION_SYNC=NOT_PERFORMED`.

## MariaDB Continuity Phase B2B-1D Package-4 — External Evidence Admission and Verification Boundary

`PHASE_B2B_1D_PACKAGE_4_EXTERNAL_EVIDENCE_ADMISSION_AND_VERIFICATION_BOUNDARY` is a
repository-only external evidence admission and verification boundary contract.
Chronology: discovery `PASS`; Architecture Freeze `PASS`; exact four-file
implementation in `core/secrets/mariadb_continuity_evidence_admission.py`,
`ops/macos/shopping/mariadb_continuity_evidence_admission_source.py`,
`tests/test_sm_mariadb_continuity_evidence_admission.py`, and
`tests/test_sm_mariadb_continuity_evidence_admission_source.py`; focused `8 passed
in 0.05s`; self-review `PASS`; Final Architecture Review `PASS` across all frozen
gates. The sandbox canonical was `2 failed, 3722 passed, 5 deselected, 481
warnings`, `RC=1`; both unrelated dashboard failures were audit-SQLite sandbox
open failures, classified `ENVIRONMENT_ONLY_FAILURE`. Host preflight established
`HOST_AUDIT_PATH_WRITABLE=YES`; authoritative supported-host canonical passed
with `3724 passed, 5 deselected, 487 warnings`, `RC=0`. No code/test correction
followed final review and no canonical rerun followed the host pass.

The contract is `repository_only=true`, `value_free=true`,
`zero_authority=true`, `zero_io=true`, `zero_network=true`, and
`fail_closed=true`. It preserves
`caller_positive_fact_injection_allowed=false`,
`arbitrary_reference_string_allowed=false`,
`actual_evidence_values_accepted=false`, and
`credential_values_accepted=false`. Reference presentation is separate from admission,
verification result, reference-local verification, evidence existence,
provenance, integrity, issuer, account/baseline binding, compatibility,
identity/lineage completeness, `RECOVER` sufficiency, Production readiness, and
authority. Current state is `reference_presented=false`,
`reference_admitted=false`, `reference_verification_required=true`,
`reference_verification_result=UNAVAILABLE`, `reference_local_verified=false`;
`authoritative_evidence_exists=false`, `provenance_valid=false`,
`integrity_binding_valid=false`, `issuer_valid=false`,
`account_binding_valid=false`, `baseline_binding_valid=false`,
`compatible=false`, `FIVE_CATEGORY_DATA_IDENTITY_COMPLETE=false`, and
`THREE_CATEGORY_CONTINUITY_LINEAGE_COMPLETE=false`. Consequently,
`recover_evidence_sufficient=false` and `production_validation_ready=false`.

This is not evidence ingestion/retrieval, authoritative verification execution,
Production access, MariaDB or credential validation, SQL, or runtime activation;
no historical evidence is claimed. Preserved truth is
`AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE=UNAVAILABLE`,
`PYMYSQL_COMPATIBILITY_EVIDENCE=UNAVAILABLE`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
`ROTATE_AUTHORIZED=false`, `REPLACE_AUTHORIZED=false`,
`STRATEGY_EXECUTED=false`, `PRODUCTION_VALIDATION_READY=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. Mac AIControlCenter remains sole Control
Plane; Ubuntu remains stateless; legacy readiness remains factual-only;
`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six Shopping actions
remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`; and
`SHOPPING_SECRET_PROVISIONING` remains target-only. Implementation commit
`9f63463dc9f1c48fdda0ceaba698fead6dd3fab2` and its normal push are `PASS`;
current HEAD and upstream are aligned at that commit with divergence `0 0`.
Documentation Git closeout remains pending, so Package-4 is not `CLOSED`.

## MariaDB Continuity Phase B2B-1D Package-3 — External Evidence Attestation Reference Contract

`PHASE_B2B_1D_PACKAGE_3_EXTERNAL_EVIDENCE_ATTESTATION_REFERENCE_CONTRACT` is
implementation-complete and validation-complete at
`1f9790fe1c96a6c20135508e4bcfbfce5d897546`. Implementation Git closeout and
push passed; the final worktree was clean with upstream divergence `0 0`.
Architecture Freeze passed. Initial focused validation was `8 passed in 0.05s`;
architecture review #1 blocked the incorrect canonical default
`VERIFIED_EXTERNAL_REFERENCE`. After correction, focused was `9 passed in
0.05s`, review #2 passed, and canonical #1 was `3716 passed, 5 deselected, 475
warnings`, `RC=0`.

Git closeout preflight later blocked because `git diff --check` found trailing
EOF blank lines in exactly two Package-3 files. The EOF-only correction passed
`SEMANTIC_CHANGE_GATE=NO_CHANGE`; post-correction architecture reconcile and
`ALL_PRIOR_ARCHITECTURE_GATES_PRESERVED` passed. Corrected canonical was `3716
passed, 5 deselected, 479 warnings`, `RC=0`. After commit and push, late focused
validation on the identical committed snapshot was `9 passed in 0.04s`; no
canonical rerun followed implementation Git closeout.

The canonical reference state is `VERIFICATION_REQUIRED`.
`VERIFIED_EXTERNAL_REFERENCE` remains a separate reference-local,
zero-promotion semantic state only. The contract and Mac projection are
repository-only, immutable, fail-closed, value-free, zero-authority, zero-I/O,
and zero-network. They accept no actual evidence values, caller-positive fact
injection, or arbitrary reference strings, and directly reuse
`EvidenceRequirementCategory`, `VerificationState`, `DataIdentityCategory`, and
`ContinuityEvidenceCategory`.

Truth remains `AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE=UNAVAILABLE`,
`PYMYSQL_COMPATIBILITY_EVIDENCE=UNAVAILABLE`,
`FIVE_CATEGORY_DATA_IDENTITY_COMPLETE=false`,
`THREE_CATEGORY_CONTINUITY_LINEAGE_COMPLETE=false`,
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`,
`ROTATE_AUTHORIZED=false`, `REPLACE_AUTHORIZED=false`,
`STRATEGY_EXECUTED=false`, `PRODUCTION_VALIDATION_READY=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. No actual historical evidence or sufficient
`RECOVER` evidence is claimed.

Mac AIControlCenter remains the sole Control Plane and Ubuntu a stateless
infrastructure worker. Legacy `production_validation_ready` remains
factual-only. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six
Shopping actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only.

Repository milestone closure remains pending final documentation review and
documentation Git closeout for exactly these six documents. This milestone
grants no Production access, MariaDB authentication, secret read, SQL execution,
PyMySQL activity, Notion sync, Production validation, or runtime activation.

## MariaDB Continuity Phase B2B-1D Package-2 — External Evidence Reference Manifest

`PHASE_B2B_1D_PACKAGE_2_EXTERNAL_EVIDENCE_REFERENCE_MANIFEST` is implemented
at `0c6cf471da9e918e798f8a71fb2d28a4afc98d46`; implementation and implementation
Git closeout are `PASS`. Focused validation returned `29 passed in 0.05s`, final
architecture review returned `PASS`, and canonical then ran exactly once and
returned `3707 passed, 5 deselected, 471 warnings`, `RC=0`. Warnings are not
failures. Neither focused nor canonical was rerun after implementation Git
closeout.

Implementation is confined to
`core/secrets/mariadb_continuity_evidence_reference_manifest.py` and
`ops/macos/shopping/mariadb_continuity_evidence_reference_source.py`; focused
coverage is in
`tests/test_sm_mariadb_continuity_evidence_reference_manifest.py` and
`tests/test_sm_mariadb_continuity_evidence_reference_source.py`.

The package is repository-only, immutable, fail-closed, value-free, and
zero-authority. It separately represents (1) evidence requirement, (2) evidence
reference state, (3) evidence existence, (4) provenance validity, (5) authority,
(6) compatibility, and (7) reference-local readiness; no one implies another.
`VerificationState` is exactly `UNAVAILABLE`, `REFERENCED_UNVERIFIED`,
`VERIFICATION_REQUIRED`, and `VERIFIED_EXTERNAL_REFERENCE`.
`VERIFIED_EXTERNAL_REFERENCE` and `reference_readiness_established` are factual,
reference-local states only. They establish neither authoritative evidence
existence, provenance authority, canonical availability, compatibility,
readiness, `RECOVER` sufficiency, Production validation readiness, nor
authorization, capability, execution, or mutation authority.

Required non-B1 evidence categories are exactly
`AUTH_PLUGIN_HISTORICAL_EVIDENCE`, `PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE`,
`EXPECTED_DATABASE_IDENTITY`, `EXPECTED_ACCOUNT_IDENTITY`, and
`REQUIRED_GRANTS_PROFILE`. The package directly reuses the frozen
`DataIdentityCategory` values `WORDPRESS_IDENTITY`, `SITE_IDENTITY`,
`APPLICATION_IDENTITY`, `CLOSED_SCHEMA_CHARACTERISTICS`, and
`CLOSED_TABLE_CHARACTERISTICS`, and directly reuses the frozen
`ContinuityEvidenceCategory` values `LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and
`PERSISTENT_VOLUME_SNAPSHOT`; no duplicate enums exist.

Frozen manifest safety is exact: `MANIFEST_VALUE_FREE=true`;
`REFERENCE_CAN_BE_CALLER_SUPPLIED=false`; `REFERENCE_ASSERTS_EXISTENCE=false`;
`REFERENCE_ASSERTS_AUTHORITY=false`; `REFERENCE_ASSERTS_COMPATIBILITY=false`;
`REFERENCE_ASSERTS_READINESS=false`; `REFERENCE_CAN_CONTAIN_SECRET_VALUE=false`;
`REFERENCE_CAN_CONTAIN_CREDENTIAL_HASH=false`;
`REFERENCE_CAN_CONTAIN_ARBITRARY_FREE_TEXT=false`; `REFERENCE_CAN_CONTAIN_SQL=false`;
`REFERENCE_CAN_TRIGGER_IO=false`; `REFERENCE_CAN_TRIGGER_NETWORK=false`; and
`REFERENCE_CAN_TRIGGER_PRODUCTION_ACCESS=false`. Source projections preserve
`authorization_authority=false`, `capability_authority=false`,
`execution_authority=false`, `mutation_authority=false`, `retry_authority=false`,
`reconnect_authority=false`, `rollback_authority=false`, and `value_free=true`.

Current state remains `AUTH_PLUGIN_STATE=UNRESOLVED`,
`AUTHORITATIVE_AUTH_PLUGIN_EVIDENCE_AVAILABLE=false`,
`PYMYSQL_COMPATIBILITY_ESTABLISHED=false`,
`FIVE_CATEGORY_DATA_IDENTITY_COMPLETE=false`,
`THREE_CATEGORY_CONTINUITY_LINEAGE_COMPLETE=false`, and
`RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`.
`HUMAN_STRATEGY_DECISION=RECOVER` was selected under
`RECOVER_DECISION_AUTHORITY_GATE=ZERO_AUTHORITY`; it supplies no execution,
Production, credential, validation, or mutation authority. `ROTATE_AUTHORIZED=false`,
`REPLACE_AUTHORIZED=false`, and `STRATEGY_EXECUTED=false`.
`FIXED_SQL_TEXT_AVAILABLE=false`, `NUMERIC_LOOPBACK_PORT_ASSIGNED=false`,
`PRODUCTION_TARGET_DEPLOYED=false`, `CONCRETE_CREDENTIAL_PATH_DEFINED=false`, and
`CREDENTIAL_VALUE_READER_IMPLEMENTED=false`.

No Production access or MariaDB authentication occurred; no secret value was
read; SQL, PyMySQL installation, and Notion sync were not performed.
Temporal truth is exactly `PRODUCTION_ACCESS_GATE=NOT_PERFORMED`,
`MARIADB_AUTHENTICATION=NOT_PERFORMED`, `SECRET_VALUES_READ=NO`,
`SQL_EXECUTION=NOT_PERFORMED`, `PYMYSQL_INSTALLED=NO`, and
`NOTION_SYNC=NOT_PERFORMED`. `PRODUCTION_VALIDATION_READY=false` and
`SHOPPING_RUNTIME_ACTIVATED=false`.
Mac AIControlCenter remains the sole Control Plane and Ubuntu an optional
stateless infrastructure worker. Legacy `production_validation_ready` remains
factual-only. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`; the exact six
Shopping actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only.

Package-2 is not yet closed at this documentation-edit step. Successful final
documentation review, commit and normal push of these exact six documents,
followed by clean-tree verification and upstream divergence `0 0`, self-activate
Package-2 closure without a second SHA-recording documentation mutation. Only
after that closeout is the next work the next MariaDB continuity
evidence/strategy boundary; it grants no Production or strategy-execution
authority.

## MariaDB Continuity Phase B2B-1D Package-1 — Zero-Authority Readiness Architecture

Package-1 implementation is complete at `cacc659fd518c751544a8062ce0c36813f1c7bcc`;
implementation Git closeout and final architecture review #3 are `PASS`.
Focused validation returned `79 passed in 0.20s`. Canonical ran exactly once on
the final reviewed code/test state: `3678 passed, 5 deselected, 467 warnings in
133.11s`, `CANONICAL_RC=0`; rerun is prohibited without a code/test change.

This is repository-safe, value-free, zero-authority readiness architecture. It
requires authoritative external historical auth-plugin evidence, makes that
evidence the single source of truth, prohibits caller overrides, and defines
compatibility-proof semantics. Current truth fails closed:
`AUTH_PLUGIN_STATE=UNRESOLVED`, authoritative evidence is unavailable, PyMySQL
compatibility is not established, and compatibility proof is unavailable. The
prior `PyMySQL==1.2.0` declaration is not installation, runtime import, or
compatibility proof; `PYMYSQL_INSTALLED=NO` and `driver_imported=false`.

Expected database/account/grants identity must be Mac-owned and independent of
credential evidence. Historical identity requires all five frozen categories:
`WORDPRESS_IDENTITY`, `SITE_IDENTITY`, `APPLICATION_IDENTITY`,
`CLOSED_SCHEMA_CHARACTERISTICS`, and `CLOSED_TABLE_CHARACTERISTICS`.
Continuity reuses exactly `LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and
`PERSISTENT_VOLUME_SNAPSHOT`, with independent historical lineage/provenance.
Insufficient `RECOVER` evidence requires a human strategy decision.

The operation profile is fixed and closed, but fixed SQL text remains
unavailable and SQL is prohibited. Production has zero mutation budget, at
most one connection/auth attempt per distinct future human authorization, no
authorization reuse, and no retry, reconnect, or rollback authority. No
aggregate Production-readiness authority exists. The Phase-A legacy
prerequisite DTO, including `production_validation_ready`, retains its legacy
semantics and is not Package-1 authority.

No Production access, MariaDB authentication/connection, credential-value
read, or SQL occurred. `compatibility_proof_available=false`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.
Mac mini AIControlCenter remains sole Control Plane; Ubuntu remains a stateless
infrastructure worker. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The exact
six Shopping actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only.

Package-1 is not yet authoritatively `CLOSED`. Closure self-activates only
after final documentation review passes, these exact six docs are committed
and normally pushed, Git is clean, and upstream divergence is `0 0`; no future
documentation commit SHA is asserted. Production validation must not start.
Next is a B2B-1D architecture/evidence boundary, not Production invocation.

## MariaDB Continuity Phase B2B-1C — Repository-Safe Concrete Readiness

`PHASE_B2B_1C` implementation is complete at
`d4802054366178c6e3282ad089e393726f2d9309` (`9 files changed`, `91
insertions`, `4 deletions`), and implementation Git closeout is `PASS`.
Focused validation returned `42 passed in 0.16s`; final architecture review was
`PASS`; canonical then ran exactly once and returned `3674 passed, 5
deselected, 463 warnings in 134.93s`, `CANONICAL_RC=0`. No focused or canonical
rerun is required unless code or tests change.

This exact six-document mutation is the documentation closeout candidate, not
an authoritative claim that all of `PHASE_B2B_1C` is closed. The phase becomes
authoritatively `CLOSED` only after this exact state passes final documentation
review, its containing documentation commit is created and normally pushed,
Git status is clean, and upstream divergence is `0 0`. Once those gates pass,
the rule is self-activating: no second documentation mutation is required
merely to write that documentation commit SHA back into these documents.

The concrete dependency declaration is exactly `PyMySQL==1.2.0` in
`requirements.txt`, with `DRIVER_FAMILY=PYMYSQL`, `DRIVER_VERSION=1.2.0`, and
`DRIVER_MODE=SYNCHRONOUS_ONE_SHOT`. Declaration does not establish installation,
import, compatibility, or readiness: `PYMYSQL_INSTALLED=NO`,
`driver_imported=false`, `PYMYSQL_COMPATIBILITY_ESTABLISHED=false`,
`AUTH_PLUGIN_STATE=UNRESOLVED`, and driver readiness remains false.

The credential boundary remains symbolic only: there is no concrete credential
path and no value was read. A future source must be fixed and closed, have a
protected parent of exact mode `0700`, a regular non-symlink leaf no broader
than `0600`, trusted uid/gid, and future FD/inode binding. Acquisition is at
most once per authorization, only after capability consumption, with no
fallback, enumeration, candidate iteration, environment or `HOME` authority,
argv/JSON/log secret transport, or secret hashing.

`ContinuityEvidenceCategory` remains the frozen B1 type with exactly
`LOGICAL_EXPORT`, `RECOVERY_ARTIFACT`, and `PERSISTENT_VOLUME_SNAPSHOT`;
`independent_historical_provenance_required=true`. B2B-1C adds no database
connection, SQL, retry, reconnect, pooling, `ControlledExecutionPort` use,
Governance semantics change, or Production authority.

Mac AIControlCenter remains the sole Control Plane and Ubuntu remains an
optional stateless infrastructure worker. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
The exact six Shopping actions remain
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains target-only.

Runtime truth remains `PRODUCTION_ACCESS_GATE=NOT_PERFORMED`,
`MARIADB_AUTHENTICATION=NOT_PERFORMED`, `SECRET_VALUES_READ=NO`,
`SQL_EXECUTION=NOT_PERFORMED`, `PRODUCTION_VALIDATION_READY=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. Production validation must not begin. After
authoritative B2B-1C closure, the next milestone remains a separate
architecture/discovery boundary, not a Production invocation.

## MariaDB Continuity Phase B2B-1A — Repository-Only Prerequisite Contracts

Milestone `PHASE_B2B_1A` is implemented at commit
`aa049e2940707ff9209a730ecfbcc5f705062171` with exactly 16 new files and 924
insertions. It adds repository-only, value-free prerequisite contracts for the
later concrete MariaDB continuity validation boundary. Implementation, focused
validation, architecture review, canonical validation, and implementation Git
closeout are `CLOSED`. The prior reviewed documentation snapshot and its
documentation Git closeout are evidenced by
`099258ce3470f57e9260a1f671b404ed9d42a623`; that commit does not contain this
six-document reconciliation.

This exact six-document reconciliation is the `FINAL CLOSURE CANDIDATE` while
it remains uncommitted. `PHASE_B2B_1A=CLOSED` becomes authoritative when the
commit containing this exact reconciliation is committed, normally pushed,
then followed by clean Git status and upstream divergence `0 0`. Once those
conditions pass, this rule records repository and documentation Git closeout as
`CLOSED` without a second documentation mutation.

The driver facts are `DRIVER_FAMILY=PYMYSQL`, `DRIVER_VERSION=1.2.0`,
`DRIVER_MODE=SYNCHRONOUS_ONE_SHOT`, `AUTH_PLUGIN_STATE=UNRESOLVED`, and
`PYMYSQL_COMPATIBILITY_ESTABLISHED=false`. The credential source remains
symbolic and Mac-Control-Plane-owned; canonical credential availability is
false, and FD/inode binding is a future concrete-source requirement. Expected
database identity, expected account identity, required grants profile,
historical data identity baseline, and historical data continuity baseline all
have `available=false`.

The fixed validation profile categories are exactly `CREDENTIAL_ACCEPTED`,
`EXPECTED_DATABASE_IDENTITY`, `EXPECTED_ACCOUNT_IDENTITY`, `REQUIRED_GRANTS`,
`EXPECTED_DATA_IDENTITY`, and `DECLARED_DATA_CONTINUITY`.
`FIXED_SQL_TEXT_AVAILABLE=false`; `ARBITRARY_SQL_ALLOWED=false`;
`MARIADB_LOOPBACK_PORT_STATE=UNASSIGNED`; `TARGET_DEPLOYED=false`.

Architecture review #1 was `BLOCKED`: `ImportFrom` AST guards inspected aliases
rather than `node.module`; an internal pytest Git assertion could not correctly
validate untracked scope; the proposed data-identity vocabulary lost some of
the five frozen B1 `DataIdentityCategory` meanings; and a duplicate
`ContinuityEvidenceCategory` made type compatibility ambiguous. The correction
handles `Import` roots through imported alias names and `ImportFrom` roots
through `node.module`, makes exact untracked scope an external Git closeout gate
rather than a permanent repository-state pytest assertion, reuses both frozen
B1 enum types directly, and explicitly tests enum identity/type reuse. Corrected
focused validation was `49 passed in
0.14s`; final architecture review #2 was `PASS`.

Canonical regression ran exactly once after final architecture `PASS`:
`3673 passed, 5 deselected, 459 warnings in 134.90s`, `RC=0`. It must not be
rerun without subsequent code/test changes. Git implementation closeout was
`PASS` at the implementation commit.

Runtime truth remains `PRODUCTION_ACCESS_GATE=NOT_PERFORMED`,
`MARIADB_AUTHENTICATION=NOT_PERFORMED`, `SECRET_VALUES_READ=NO`,
`SQL_EXECUTION=NOT_PERFORMED`, `DOCKER_ACCESS=NOT_PERFORMED`,
`COLIMA_ACCESS=NOT_PERFORMED`, `PRODUCTION_AUTHORIZATION_CONSUMED=NO`,
`PYMYSQL_INSTALLED=NO`, `REQUIREMENTS_CHANGED=NO`, and
`NOTION_SYNC=NOT_PERFORMED`. Thus `PRODUCTION_VALIDATION_READY=false` and
`SHOPPING_RUNTIME_ACTIVATED=false`.

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
infrastructure worker and receives no AI workload, business logic, application
state, or governance authority. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.
The exact six actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
`SHOPPING_SECRET_PROVISIONING` remains target-only, not a seventh action.

Next is `PHASE_B2B_1B_CONCRETE_READINESS_DISCOVERY`. It must begin read-only and
implies no PyMySQL installation, requirements change, Production access,
MariaDB authentication, credential acquisition, SQL execution, numeric
loopback-port deployment, or runtime activation.

## MariaDB Continuity Phase B2A — Value-Free Continuity Contracts

Status: `PHASE_B2A_IMPLEMENTATION_STATUS=CLOSED`,
`PHASE_B2A_VALIDATION_STATUS=CLOSED`,
`PHASE_B2A_DOCUMENTATION_STATUS=CLOSED`, and
`PHASE_B2A_REPOSITORY_STATUS=CLOSED`. Implementation commit:
`6063ce08b62e99331f5d442afc9d2a71703bcabf`. Documentation closeout commit:
`cfb1d7eae4b9676373ba31c485330b8449cd90f3`.

Phase B2A adds value-free MariaDB continuity contracts only. Canonical current
truth remains separate from constructible runtime observations.
`MariaDBContinuityRuntimeObservation` supports exactly `CONFIRMED`, `REJECTED`,
`NOT_EVALUATED`, and `UNCERTAIN`; `complete_validation` is true only when all
six mandatory runtime facts are `CONFIRMED`. Every projection grants zero
authorization, capability, execution, mutation, retry, reconnect, and rollback
authority.

Protected-source validation is metadata-only for one fixed slot. The parent
must be a `0700` directory, non-symlink, with expected uid and gid. The leaf
must be a non-empty regular non-symlink file, have permissions no broader than
`0600`, and have expected uid and gid. `ProtectedSourceReason` is closed;
contradictory `ProtectedSourceObservation` construction is rejected. A
logically consistent manually constructed positive observation is only an
inert, value-free factual/fake DTO and grants no readiness or authority.
Trusted filesystem evidence is produced separately by
`observe_fixed_protected_source`. No credential value is read; there is no
enumeration or fallback.

The target remains `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE`, owned by
`MAC_CONTROL_PLANE`, with `numeric_loopback_port_assigned=false`,
`target_deployed=false`, and `production_target_ready=false`. No numeric
MariaDB loopback port is assigned. The driver contract is `DRIVER_FAMILY=PYMYSQL`,
`DRIVER_VERSION=1.2.0`, `DRIVER_MODE=SYNCHRONOUS_ONE_SHOT`,
`AUTH_PLUGIN_STATE=UNRESOLVED`, and
`maximum_future_connection_count_per_authorization=1`. Actual PyMySQL import
and installation are absent; `requirements.txt` is unchanged. Phase B2A has no
network, SQL, retry, reconnect, or pooling.

Exact production files are `core/secrets/mariadb_continuity_observations.py`,
`ops/macos/shopping/mariadb_continuity_protected_sources.py`,
`ops/macos/shopping/mariadb_continuity_pymysql_adapter.py`, and
`ops/macos/shopping/mariadb_continuity_target_resolver.py`. Exact test files are
`tests/test_sm_mariadb_continuity_observations.py`,
`tests/test_sm_mariadb_continuity_protected_sources.py`,
`tests/test_sm_mariadb_continuity_pymysql_adapter.py`, and
`tests/test_sm_mariadb_continuity_target_resolver.py`.

Validation history: initial focused `21 passed in 0.35s`; first final
architecture review `BLOCKED`; corrected focused `31 passed in 0.13s`; final
read-only architecture review #2 `PASS`; canonical exactly once on the final
reviewed code/test state, `3624 passed, 5 deselected, 455 warnings in 134.66s`,
`RC=0`. Focused and canonical reruns after the implementation commit were both
`NOT_RUN`.

The normal implementation push, final Git clean check, and final upstream
divergence `0 0` passed. A second implementation-closeout invocation was
rejected fail-closed because its expected pre-commit HEAD was stale after the
successful commit. This was successful duplicate-closeout protection: it made
no second commit, second push, or implementation change.

Runtime truth remains `PRODUCTION_ACCESS_GATE=NOT_PERFORMED`,
`MARIADB_AUTHENTICATION=NOT_PERFORMED`, `SECRET_VALUES_READ=NO`,
`SQL_EXECUTION=NOT_PERFORMED`, `DOCKER_ACCESS=NOT_PERFORMED`,
`COLIMA_ACCESS=NOT_PERFORMED`, `NOTION_SYNC=NOT_PERFORMED`,
`PYMYSQL_INSTALLED=NO`, `REQUIREMENTS_CHANGED=NO`,
`AUTH_PLUGIN_STATE=UNRESOLVED`, `MARIADB_LOOPBACK_PORT_STATE=UNASSIGNED`,
`PRODUCTION_VALIDATION_READY=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
infrastructure worker. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The exact
six actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
`SHOPPING_SECRET_PROVISIONING` remains target-only. Repository closeout is
complete. The next development boundary is `PHASE_B2B_CONCRETE_INTEGRATION_DISCOVERY`;
Phase B2B is not implemented here.

## MariaDB Continuity Phase B1 — Factual Attempt and Contract Architecture

Status: **IMPLEMENTATION-COMPLETE AND VALIDATION-COMPLETE** at implementation
commit `acdbd859872b842691c293b5e094472b344d304b`.

Phase B1 defines a one-shot factual attempt lifecycle:
`NEW -> AUTHORIZED -> CONSUMED -> PRE_ATTEMPT -> ATTEMPT_INITIATED -> TERMINAL`.
`PRE_ATTEMPT -> TERMINAL` preserves `attempted_count=0`, while
`ATTEMPT_INITIATED -> TERMINAL` preserves `attempted_count=1`. Skipped,
reverse, repeated, and post-terminal transitions are prohibited; no second
attempt exists. `AUTHORIZED` is factual only and grants no authority.

The frozen, value-free source categories are exactly `CREDENTIAL_SOURCE`,
`EXPECTED_IDENTITY_DESCRIPTOR`, `DATA_IDENTITY_BASELINE`, and
`DATA_CONTINUITY_BASELINE`. Current availability remains
`credential_material_available=false`,
`expected_identity_descriptor_available=false`,
`data_identity_baseline_available=false`, and
`data_continuity_baseline_available=false`. Supported public construction can
neither supply unsupported positive availability nor construct contradictory
source availability.

The credential contract remains Mac-Control-Plane-owned and uses one external,
protected, fixed slot outside Git: a `0700` protected parent and a `0600`
regular non-symlink file with explicitly trusted uid/gid. Ambient `HOME`/UID,
environment, argv, JSON secret-value transport, Governance transport, secret
logging/hashing, fallback, enumeration, and candidate iteration grant no
authority and are prohibited. Acquisition is permitted at most once and only
after capability consumption. No actual credential material was verified or
read.

The target is `CLOSED_SYMBOLIC_PRODUCTION_MARIADB_PROFILE`, owned by
`MAC_CONTROL_PLANE`. Current facts are
`canonical_target_contract_defined=true`,
`numeric_loopback_port_assigned=false`, `target_deployed=false`, and
`production_target_ready=false`. Readiness is derived only as
`numeric_loopback_port_assigned AND target_deployed`. Callers provide no host,
port, DSN, URL, database, or username; Phase B1 assigns no numeric MariaDB port.

Phase B1 contains no PyMySQL, MariaDB driver, SQL, network access, filesystem
credential-source implementation, environment/argv credential transport,
retry, reconnect, pooling, Production access, or MariaDB authentication.
`PRODUCTION_VALIDATION_READY=false`; `SHOPPING_RUNTIME_ACTIVATED=false`.
Production access, authentication, runtime inspection, Docker, Colima, and
Notion sync were `NOT_PERFORMED`; secret values read: `NO`. PyMySQL was not
installed and requirements were unchanged.

Preservation gate: `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The exact six
actions remain `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
`SHOPPING_SECRET_PROVISIONING` remains a target only. Mac AIControlCenter
remains the sole Control Plane; Ubuntu remains a stateless infrastructure
worker.

Validation history is intentionally complete: initial focused validation was
`22 passed in 0.07s`; the first architecture review was `BLOCKED` because
public factual forgeability, contradiction handling, and associated test
coverage were insufficient. The correction passed; corrected focused
validation was `37 passed in 0.06s`; final read-only architecture review was
`PASS`: `SOURCE_FACT_FORGEABILITY_GATE=PASS`,
`SOURCE_CONTRADICTION_REJECTION_GATE=PASS`,
`TARGET_FACT_FORGEABILITY_GATE=PASS`,
`TARGET_CONTRADICTION_REJECTION_GATE=PASS`, `DERIVED_READINESS_GATE=PASS`, and
`TEST_QUALITY_GATE=PASS`. Canonical ran exactly once after the final reviewed
code/test state: `3593 passed, 5 deselected, 447 warnings in 133.58s`, `RC=0`.
A post-implementation-commit canonical rerun was `NOT_RUN`.

Phase B2 is future work only. It may address PyMySQL selection/pinning, a
synchronous one-shot Mac driver adapter, fixed loopback target resolution, a
protected credential reader, independent expected DB/account/grants and data
identity/continuity baseline readers, and fixed parameterized read-only SQL,
with one connection and no retry, reconnect, or pooling. It is neither
implemented nor Production-ready, and no new numeric SM-01B-02D identifier is
assigned here.

## MariaDB Continuity Validation Prerequisite / Phase A

Status: repository-complete after documentation closeout. Implementation commit:
`ccf3ce00f7f6602d2cc6a84ec5632c7088cae418`.

Phase A adds only value-free MariaDB continuity prerequisite/readiness facts and
a process-local composition boundary owned by the Mac AIControlCenter Control
Plane. Its `HumanPresenceGrant` is non-serializable and one-shot: direct
construction is prohibited, only private inert Phase-A test issuance exists,
requests are canonically bound, concurrent use is exactly-once, and the grant is
consumed before assembly and remains consumed if assembly fails. Exceptions are
redacted, and composition invokes no capability.

Phase A adds no MariaDB driver, Production credential source, credential
material verification, SQL, network connectivity, canonical deployed
Mac-reachable MariaDB target, identity or continuity baseline, real Production
validation capability, Production authentication, consumer compatibility
validation, mutation authority, or runtime activation. Consequently,
`PRODUCTION_VALIDATION_READY=false`, `SHOPPING_RUNTIME_ACTIVATED=false`, and
historical MariaDB credential continuity remains unresolved.

`SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`. The exact six Shopping secret
provisioning actions and the Mac AIControlCenter sole-Control-Plane/Ubuntu
stateless-worker architecture are preserved.

Evidence: focused validation `13 passed in 0.07s`; final architecture review
`FINAL_PHASE_A_ARCHITECTURE_REVIEW_GATE=PASS`; canonical regression `3556
passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly once on the final
reviewed implementation tree. The canonical rerun after the implementation
commit was `NOT_RUN`. Production access and MariaDB authentication were
`NOT_PERFORMED`; runtime, Docker, Colima, and Notion access were
`NOT_PERFORMED`; secret values read: `NO`.

## SM-01B-02D-06 — MariaDB Historical Credential Continuity Validation Boundary v1

Status: CLOSED at implementation commit
`3c93ad39586080db618ee090a7548806c024c44a`. This is a Mac mini M4
AIControlCenter-owned, value-free, read-only MariaDB historical credential
continuity validation boundary. It is neither a Production mutation boundary
nor `ControlledExecutionPort`, uses no `GovernanceMutationBudget`, and grants
zero mutation, authorization, execution, retry, or rollback authority. Its
result and evidence are factual metadata only.

The exact outcomes are `VALIDATED`, `REJECTED`, `UNAVAILABLE`, `UNSAFE`,
`MALFORMED`, and fail-closed `UNCERTAIN`. `VALIDATED` requires
`attempted_count=1` plus separate `CONFIRMED` factual observations for
credential acceptance, expected database identity, expected account identity,
required grants, data identity, and data continuity. Authentication acceptance
alone is insufficient; consumer compatibility remains `NOT_EVALUATED`. There
is no automatic retry, fallback credential, candidate iteration, credential
guessing, automatic rollback, or compensation.

The future Production access capability is externally supplied,
non-factual, non-serializable authority metadata. It is absent from the
request, result, and projection, is not minted by core, and may be invoked at
most once per application validation invocation. This implementation adds the
domain and port in `core/secrets/mariadb_continuity_validation.py` and
`core/secrets/mariadb_continuity_validation_port.py`, plus the outer adapter in
`ops/macos/shopping/mariadb_continuity_validation_adapter.py`. It implements no
real MariaDB client and no real Production capability.

There is no change to `AuthorizationConsumptionPort`, durable SQLite
authorization consumption, Governance execution semantics, SEC-02,
postcondition semantics, Governance audit/evidence,
`ShoppingProvisioningGovernanceCoordinator`, config, schemas, or SM-01B-02D-05
`ContinuityDecision`. No seventh action was added. The exact six existing
Shopping provisioning actions remain
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`;
`SHOPPING_SECRET_PROVISIONING` remains a target identifier, not an action.

No Production MariaDB authentication or historical-credential validation
occurred, so continuity remains `UNRESOLVED`. No `RECOVER` confirmation,
`ROTATE`, `REPLACE`, DB account/grant or encrypted-payload mutation, secret
materialization, WordPress/WooCommerce DB-client cutover, runtime cutover, or
old-account retirement occurred; `SHOPPING_RUNTIME_ACTIVATED=false`. Phase B
architecture discovery is the next development boundary and must precede any
future, separately explicitly human-authorized Production validation. The 06
implementation itself authorizes no such operation.

Focused validation: `33 passed in 0.08s`. Final architecture review: `PASS`,
`CRITICAL=NONE`, `HIGH=NONE`, `MEDIUM=NONE`, `LOW=NONE`. The canonical
regression gate was accidentally executed twice on the same unchanged,
final-reviewed implementation tree; both runs reported `3543 passed`, `5
deselected`, `447 warnings`, `RC=0`. This duplicate execution is an operational
process deviation, not a code or architecture failure, and no code or test
change occurred between runs. Implementation push: `PASS`; final Git clean,
upstream divergence `0 0`. Production access, runtime inspection, Docker,
Colima, and Notion sync: `NOT_PERFORMED`. Secret values read: `NO`.

Mac mini M4 AIControlCenter remains the sole Control Plane; Ubuntu remains a
stateless infrastructure worker. No authority is delegated to WordPress,
WooCommerce, n8n, Ubuntu, MariaDB, or external recovery custody systems.

## SM-01B-02D-05 — MariaDB Credential Continuity Decision Model v1

Status: CLOSED. Implementation commit:
`9f168cc475345e7d2c949f375ef5c44f2ad2fda9`. `ContinuityDecision` is a
fail-closed public factual decision model. Its exact states are `UNRESOLVED`,
`STRATEGY_DECLARED`, `VALIDATION_REQUIRED`, and `RESOLVED`; its exact
strategies are `RECOVER`, `ROTATE`, and `REPLACE`. `RESOLVED` and caller-supplied
`validation_confirmed` are factual metadata only. Neither grants authority,
and trustworthy Production acquisition of validation confirmation remains a
future separately bounded validation concern. Strategy selection grants zero
authority. `mutation_authority` remains `false`; `capability_id` remains
`null`.

The model stores and transports no credential or secret value. It introduces
no password, username, secret-derived hash/digest, private identity, recipient
value, arbitrary path, environment value, stdout/stderr, command, argv,
executable, callback, port, authorization, mutation budget, execution request,
or execution receipt. The six existing Shopping provisioning actions remain
exactly `SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`,
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`.
`SHOPPING_SECRET_PROVISIONING` is a target identifier, not a seventh action.

No change was made to `AuthorizationConsumptionPort`, durable SQLite
authorization consumption, mutation budgets, `ControlledExecutionPort`,
SEC-02 semantics, postcondition semantics, Governance audit/evidence,
`ShoppingProvisioningGovernanceCoordinator`, `secret_provisioning_adapters.py`,
config, schema, or inspectors. This milestone implements no Production
credential validation or execution, including `RECOVER`,
`MARIADB_CREDENTIAL_ROTATE`, `MARIADB_CREDENTIAL_REPLACE`, recovery, rotation,
replacement, DB secret payload creation/materialization, DB-dependent
validation, WordPress/WooCommerce DB cutover, runtime cutover, or
`SHOPPING_RUNTIME_ACTIVATED`. It does not claim historical credentials were
recovered, validated, rotated, replaced, materialized, or activated.

Mac mini M4 AIControlCenter remains the sole Control Plane. Ubuntu remains a
stateless infrastructure worker; no authority is delegated to WordPress,
WooCommerce, n8n, Ubuntu, or external recovery custody systems. Focused
validation: `39 passed in 0.04s`. Canonical validation: `3510 passed`, `5
deselected`, `447 warnings`, `RC=0`. Final architecture review: `PASS`, with
`CRITICAL=NONE`, `HIGH=NONE`, `MEDIUM=NONE`, and `LOW=NONE`. Implementation
push: `PASS`. Production access: `NOT_PERFORMED`. Notion sync: `NOT_PERFORMED`.

## SM-01B-02D-04B — Provisioning Runtime Composition & Read-Only Postconditions v1

Status: CLOSED at implementation commit `a4cb53d5398dffdc33366ac042fdb7813f6d4577`
(`feat(shopping): add secret provisioning readiness composition`). The Mac mini
M4 AIControlCenter remains the sole Control Plane; Ubuntu remains an optional
stateless infrastructure worker. The composition is read-only, JSON-first,
deterministic, structural, and value-free: it exposes no secret/recipient
values, private identities, arbitrary paths, stdout/stderr, environment values,
or mutation authority.

The closed readiness vocabulary is `READY`, `MISSING`, `BLOCKED`, `UNSAFE`,
and `MALFORMED`. For secret payloads and runtime dependencies,
configured/ready false/false maps to `MISSING`, true/false to `BLOCKED`,
true/true to `READY`, and contradictory false/true to fail-closed `MALFORMED`;
malformed state blocks overall readiness and activation. File/executable
observations remain structural.

All six provisioning actions remain unchanged; offline recovery intake and
registration remain separate. Governance authorization, durable consumption,
and `ControlledExecutionPort` semantics are unchanged. No mutation API, secret
payload, materialization, or runtime cutover was added or performed;
`materialization_implemented=false` and `SHOPPING_RUNTIME_ACTIVATED=false`.
Historical MariaDB credential continuity remains unresolved and blocks DB
payload readiness/materialization, DB-dependent validation,
WordPress/WooCommerce DB cutover, runtime cutover, and activation. 04B claims
neither recovery nor replacement; a dedicated Shopping secret-materialization
coordinator/adapter/capability architecture remains future work.

Validation recorded focused `47 passed`; canonical `3471 passed, 5 deselected,
447 warnings` in approximately `133.97s`, `CANONICAL_RC=0`, and
`CANONICAL_GATE=PASS`. Implementation push, final clean, upstream divergence
`0 0`, and closeout gates passed. Production access and Notion sync were not
performed. Canonical was not rerun for documentation closeout.

## SM-01B-02D-04A — Governed Offline Public Recipient Intake v1

Implementation and validation are complete at commit
`6e1aa0135b652b199f05a4911c0f45817a8529f4`; documentation closeout is complete and 04A is CLOSED. The canonical provisioning definition now
contains the exact sixth action
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE`. It accepts one typed,
value-redacted, syntactically valid age public recipient and performs one
bounded Governance-controlled intake mutation into the Mac Control Plane's
fixed inbox. The existing later action remains
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`.

**Intake and registration are separate actions.** Each requires a separate
fresh human authorization, mutation budget, execution request, and durable
authorization-consumption record. One authorization never covers both. The
flow is external offline-recovery custody -> already-public age recipient
metadata -> bounded intake -> fixed Control Plane inbox -> later separately
authorized registration.

The private offline-recovery identity remains external to the Production Mac:
it is never generated or stored there, never read by Python, and never queried
from the Production Mac. Only already-public age recipient metadata may enter
AIControlCenter. The canonical no-clobber, public-recipient-only inbox policy is
base `control-plane-home`, relative path
`.config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt`, outside
Git, owned by the expected Control Plane uid/gid, with mode no broader than
`0600`. No generic file-write, arbitrary destination-path, or arbitrary
shell/argv API is exposed, and parent directories are never created implicitly.

Before any filesystem mutation, the typed boundary proves exactly one bounded
syntactically valid age public recipient and the fixed trusted age executable
prevalidates it. The fixed existing parent chain is then traversed
descriptor-relative with no-follow/directory semantics; every directory is
checked with `fstat` for expected ownership and safe mode. The leaf is created
with exclusive no-follow semantics (`O_CREAT | O_EXCL | O_NOFOLLOW`), and the
mutation boundary is crossed immediately after successful creation. From that
point, any inability to prove the result is `UNCERTAIN`, with no automatic
deletion or cleanup.

Created-leaf metadata is verified on its descriptor: regular-file type,
expected uid/gid, mode no broader than `0600`, bounded expected size, and
`st_dev`/`st_ino` identity. Postcondition validation performs a fresh trusted
parent traversal. The original and fresh final-parent device/inode identities
must match, and the canonical leaf device/inode must match the leaf actually
created. Parent or path rebinding therefore cannot be classified
`COMPLETED`. There is no retry, rollback, compensation, repair, recovery,
claim stealing, lease recovery, or stranded-claim recovery; evidence remains
value-free and excludes recipient contents, secrets, stdout, stderr,
environment values, and private identity material.

Mac mini M4 remains the sole Brain and Control Plane. AIControlCenter remains
the single orchestration, Governance, policy, authorization, audit, and
business-logic authority. Ubuntu remains only a stateless infrastructure
worker: it owns no AI workload, business logic, Governance state, application
state, or Control Plane authority.

Production semantics remain one human authorization = one bounded Production
mutation. Authorization consumption is factual evidence and grants zero
execution authority. After consumption, the coordinator recollects current
read-only preconditions, compares current state, reruns SEC-02, requires
`ALLOW_SINGLE_INVOCATION`, and invokes exactly one `ControlledExecutionPort`
action. `FAILED` and `UNCERTAIN` both consume authorization; any retry is an
entirely new Production mutation attempt. Automatic retry, authorization
reuse, automatic external rollback, and compensation remain prohibited.

`SM-01B-02D-03` remains CLOSED. 04A changed neither the durable
`AuthorizationConsumptionPort`, its SQLite adapter or path policy, nor core
durable-consumption semantics; `CORE_GOVERNANCE_SEMANTICS_CHANGE_REQUIRED=false`.

Validation recorded focused `163 passed` and canonical `3457 passed, 5
deselected, 447 warnings in 133.23s`, `RC=0`; the warnings are not 04A
failures. Implementation Git closeout passed at the commit above with a clean
tree and upstream divergence `0 0`.

No Production filesystem mutation, real recipient intake, SOPS or age
installation, Control Plane identity creation, recipient registration, or
runtime cutover occurred during implementation or validation.
`SHOPPING_RUNTIME_ACTIVATED=false`; Notion remains deferred until that
milestone. Historical MariaDB credentials remain unresolved. SOPS+age does not
recover them. This did not block 04A, but it still blocks DB-secret payload
creation with historical credentials, DB-secret materialization,
database-dependent validation, WordPress/WooCommerce DB cutover, runtime
cutover, and `SHOPPING_RUNTIME_ACTIVATED`. 04B is CLOSED as documented above.

## SM-01B-02D-03 — Durable Authorization Consumption & Evidence Store v1

Validated at `SM_01B_02D_03_DURABLE_AUTHORIZATION_CONSUMPTION_VALIDATED=true`;
implementation commit `681a9e342fde47c7bcb9d3aa2d497b737a19e052`. This is generic
Governance owned by the Mac AIControlCenter Control Plane, not Shopping business
logic or Ubuntu state. `AuthorizationConsumptionPort` is unchanged and
`CORE_SEMANTICS_CHANGE_REQUIRED=false`.

The Governance-owned SQLite adapter keeps Production state external to
Git/source at
`~/Library/Application Support/AIControlCenter/governance/authorization-consumption.sqlite3`.
It validates path ownership, does not mutate or force the shared application-state
parent to `0700`, and enforces Governance subtree `0700` and database `0600`.
A durable `DURABLY_CLAIMED` barrier precedes the final transaction, which
atomically records authorization `CONSUMED`, mutation budget `CONSUMED`, zero
invocation/completed/uncertain accounting, and a `COMMITTED` receipt. Protected
lifecycle, authorization, budget, claim, execution, request, and decision
identities use replay-protected, value-free canonical binding/integrity digests;
no secret values persist.

A new `consume_once` after `COMMITTED` fails closed as repeated consumption and
never returns a historical `AuthorizationConsumptionResult`. A stranded
`DURABLY_CLAIMED` record fails closed. There is no claim stealing, lease,
expiry, automatic recovery, retry, rollback, or compensation. Only the same
invocation with ambiguous final commit acknowledgement may reconcile, and only
when its exact expected `COMMITTED` record validates.

Consumption evidence grants no execution authority; remaining budget is
accounting, not retry authority. Callers must recollect/recompare current
read-only preconditions and rerun SEC-02. `ControlledExecutionPort` may run only
after `ALLOW_SINGLE_INVOCATION`; replay cannot resurrect invocation authority.

Validation recorded focused `372 passed`; corrected-tree canonical `3433
passed, 5 deselected, 447 warnings in 135.93s`, `RC=0`, executed exactly once
after final fixture correction. Implementation Git closeout PASS;
implementation pushed; upstream divergence `0 0`.
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, `NOTION_SYNC=false`, and
`SHOPPING_RUNTIME_ACTIVATED=false`.

SM-01B remains incomplete and no Production provisioning occurred. SOPS/age
installation, control-plane age identity creation, recipient registration,
secret payload/materialization, and runtime activation remain outstanding.
Historical MariaDB credential continuity remains unresolved; SOPS+age does not
recover historical credentials. The offline-recovery private identity remains
external to the Production Mac; only public recipient metadata may enter the
Mac Control Plane, and the operational public-recipient inbox/intake write
boundary requires explicit governance before Production activation. Notion
remains deferred until `SHOPPING_RUNTIME_ACTIVATED`.

## SM-01B-02D-02B — Shopping Secret Provisioning Capabilities v1

Status: implementation, validation, and Git closeout complete at
`SM_01B_02D_02B_SECRET_PROVISIONING_CAPABILITIES_VALIDATED=true`.
Implementation commit: `bffe28a153eb83d3c61e04d38f2ab96892a6feb5`.

Five narrow Shopping secret provisioning capabilities are validated. They use
explicit `expected_uid` injection with no ambient UID or HOME authority and a
fixed, trusted Homebrew executable boundary. No generic shell or argv execution
API is exposed. Existing targets are protected by no-overwrite/no-clobber
behavior; mutation uncertainty fails closed; and there is no automatic retry,
rollback, or compensation. Python does not read the private control-plane age
identity to derive recipients. Offline recovery remains limited to public
recipient metadata, and the value-free evidence contract remains intact.

Focused validation recorded `421 passed`. Canonical regression recorded `3387
passed, 5 deselected, 447 warnings in 132.49s`, `RC=0`, with canonical execution
count exactly `1`. Git closeout: PASS. Upstream divergence: `0 0`.
`PRODUCTION_MUTATION=false`, `AUTHORIZATION_CONSUMED=false`,
`SECRET_VALUES_READ=false`, `RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`,
`COLIMA_ACCESS=false`, and `NOTION_SYNC=false`.

Actual SOPS/age installation, age identity creation, recipient registration,
secret materialization, and runtime activation have not occurred. Historical
MariaDB credential continuity remains explicitly unresolved.
`SHOPPING_RUNTIME_ACTIVATED` remains the future Production milestone. Notion
remains deferred until after Runtime Activation. Next engineering recommendation:
`SM-01B-02D-03 — Durable Authorization Consumption & Evidence Store v1` —
generic Governance-owned, Mac Control Plane only, replay-safe and durable, with
no Shopping business logic.

## SM-01B-02D-01B — Shopping Provisioning Governance Coordinator v1

Status: implementation and validation complete at
`SM_01B_02D_01B_SHOPPING_PROVISIONING_GOVERNANCE_COORDINATOR_VALIDATED`.
Implementation commit: `8229288d68d46383082cec48ffc726bd0dbee09a`.

The coordinator enforces planner -> explicit human-authorized lifecycle ->
read-only precondition -> SEC-02 `ALLOW_AUTHORIZATION_CONSUMPTION` ->
`AuthorizationConsumptionPort.consume_once` -> fresh read-only precondition ->
SEC-02 `ALLOW_SINGLE_INVOCATION` -> exactly one of five bounded
`ControlledExecutionPort` adapters -> read-only postcondition -> closeout or
stop. Consumption evidence grants no execution authority. `READY`, `BLOCKED`,
or `MALFORMED` causes zero consumption and zero invocation. Post-consumption
drift stops with consumed authorization and zero invocation. `FAILED` or
`UNCERTAIN` stops after one attempt. There is no automatic retry, rollback, or
compensation.

Focused validation recorded `181 passed`. Canonical regression recorded `3349
passed, 5 deselected, 447 warnings`, `RC=0`, with canonical execution count
exactly `1`. This validation activity recorded `PRODUCTION_MUTATION=false`,
`AUTHORIZATION_CONSUMED=false`, `SECRET_VALUES_READ=false`,
`RUNTIME_INSPECTION=false`, `DOCKER_ACCESS=false`, `COLIMA_ACCESS=false`,
`MATERIALIZATION_IMPLEMENTED=false`, and `NOTION_SYNC=false`. Historical
MariaDB credential continuity remains unresolved; `SHOPPING_RUNTIME_ACTIVATED`
remains the Production milestone.

Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless
worker. Core has no dependency on `ops.macos`, and no generic shell or argv
execution API exists. Next engineering milestone:
`SM-01B-02D-02 — Concrete Provisioning Capabilities v1`.

## SM-01B-02C — Bounded Mutation Adapters v1

Status: implementation and validation complete at milestone
`SM_01B_02C_BOUNDED_MUTATION_ADAPTERS_VALIDATED`, implementation commit
`5a811cb1f9c782acb4f3e537596fb47ae0c599ff`.

SM-01B-02C implements bounded mutation adapter code only for the exact
`SHOPPING_SECRET_PROVISIONING` target and these five exact actions:
`SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE`,
`SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE`,
`SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE`,
`SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE`, and
`SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE`. The adapters
reuse SEC-02 `ControlledExecutionPort`, accept only the exact target and exact
action, and invoke at most one narrow injected capability. They do not issue
or consume authorization, retry, rollback, or compensate. They produce
value-free `GovernanceExecutionReceipt` evidence with a deterministic,
injective receipt-identity namespace over the full `execution_request_id`.
Offline-recovery private custody remains external. There is no generic
shell/argv/package-manager execution framework and no parallel governance
framework.

Mac AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless
infrastructure worker with no Shopping secret ownership. Historical MariaDB
credential continuity remains unresolved; this milestone does not recover,
rotate, replace, derive, invent, or validate historical credentials.

Production truth remains `production_status=NOT_DEPLOYED`;
`materialization_implemented=false`; `SOPS_INSTALLATION=false`;
`AGE_INSTALLATION=false`; `AGE_KEY_GENERATION=false`;
`OFFLINE_RECOVERY_KEY_GENERATION=false`; `SECRET_PAYLOAD_CREATION=false`;
`SECRET_MATERIALIZATION=false`; `AUTHORIZATION_CONSUMED=false`;
`RUNTIME_INSPECTION=false`; `PRODUCTION_MUTATION=false`;
`SHOPPING_RUNTIME_ACTIVATED=false`.

Final implementation evidence recorded focused `128 passed` and canonical
`3288 passed, 5 deselected, 447 warnings`, `RC=0`, executed exactly once on
final implementation code. Exact three-file implementation scope,
post-canonical scope, staged scope, staged diff check, commit, push, and
upstream alignment `0 0` all passed. Next development milestone:
`SM-01B-02D — Authorized Toolchain & Identity Provisioning v1`. Adapter
implementation is not authorization to execute adapters. Each future
Production mutation requires separate human authorization immediately before
exactly one bounded invocation, with no automatic retry or rollback. SM-01B
overall remains incomplete.

## SM-01B-02B — Provisioning Planner v1

Status: implementation and validation complete at milestone
`SM_01B_02B_PROVISIONING_PLANNER_VALIDATED`, implementation commit
`2330eca7e8ed99ba50cb9f99bad1abba4a4d9876`.

The canonical provisioning definition and its Draft 2020-12 schema define
exactly five typed actions. Core `ProvisioningPlan` is vendor-neutral and
value-free. Malformed input emits only sanitized `UNKNOWN_ACTION` or
`MALFORMED_CONFIGURATION` evidence. The read-only macOS provisioning inspector
performs planning only; it does not execute a plan. Core imports from `ops` and
`integrations` remain zero. Future execution must reuse SEC-02
`ControlledExecutionPort` and must not create a parallel governance framework.

AIControlCenter on the Mac remains the sole Control Plane. Ubuntu remains a
stateless worker with no Shopping secret ownership. Offline-recovery custody
remains external. Historical MariaDB credential continuity remains unresolved;
SM-01B-02B does not recover, replace, rotate, or invent historical credentials.
Production truth remains `NOT_DEPLOYED` and
`materialization_implemented=false`.

`SOPS_INSTALLATION=false`, `AGE_INSTALLATION=false`,
`AGE_KEY_GENERATION=false`, `OFFLINE_RECOVERY_KEY_GENERATION=false`,
`SECRET_PAYLOAD_CREATION=false`, `SECRET_MATERIALIZATION=false`,
`AUTHORIZATION_CONSUMED=false`, `RUNTIME_INSPECTION=false`,
`PRODUCTION_MUTATION=false`, and `SHOPPING_RUNTIME_ACTIVATED=false`.

Final implementation evidence recorded `73 passed` focused and `3236 passed,
5 deselected, 447 warnings`, `RC=0` canonical regression, executed exactly once
on final implementation code. Exact six-file implementation scope,
post-canonical scope, staged scope, staged diff check, commit, push, and
upstream alignment all passed. Next development milestone:
`SM-01B-02C — Bounded Mutation Adapters v1`. Implementing adapters is not
authorization to execute them. SM-01B overall remains incomplete.

## SM-01B-01 — SOPS/age Secret Backend Inspection v1

Status: implementation and validation complete at milestone
`SM_01B_01_SECRET_BACKEND_INSPECTION_VALIDATED` and implementation commit
`1ada572a75cf4313f65288e81134777948900cda`.

SOPS+age is the selected replaceable Shopping secret-backend architecture; it
is not deployed. The canonical definition and schema are
`config/shopping-secret-backend.json` and
`config/schemas/shopping-secret-backend.schema.json`. The vendor-neutral port
is `core/secrets/ports.py`; SOPS+age details remain in the read-only macOS
outer adapter `ops/macos/shopping/sops_age_backend.py`. Core imports from
`ops` and `integrations` remain zero.

AIControlCenter on the Mac remains the sole Control Plane. Ubuntu remains a
stateless infrastructure worker and owns no Shopping secrets. Identity custody
is portable from injected `control_plane_home` plus
`.config/sops/age/keys.txt`; no concrete user path is canonical. The adapter
discovers no HOME, environment, pwd, Keychain, runtime, Docker, Colima, or
network state. It performs metadata-only `lstat` inspection and reads neither
the identity nor encrypted payload contents. The canonical logical encrypted
payload path is `deploy/shopping/secrets/shopping.enc.yaml`. Its metadata
policy requires `control-plane` and `offline-recovery` recipients without
storing recipient material in the definition. Schema and runtime safety
validation are aligned.

Production truth remains `NOT_DEPLOYED`; SOPS installation, age installation,
age key generation, encrypted payload provisioning, secret materialization,
and Production mutation did not occur. `materialization_implemented=false` and
`SHOPPING_RUNTIME_ACTIVATED=false`. No secret values, Keychain, or Production
runtime were inspected. Historical MariaDB credential continuity remains
unresolved: this architecture cannot recover or silently replace historical
credentials, and runtime cutover remains blocked on an explicit continuity,
recovery, or rotation strategy. Next: `SM-01B-02 — SOPS/age Toolchain &
Identity Provisioning`; SM-01B overall is not complete.

## SM-01A — Shopping Secret Contract & Fail-Closed Preflight v1

SM-01A is implementation- and validation-complete. The value-free JSON
contract at `deploy/shopping/config/secret-contract.json` is the single
canonical Shopping secret-metadata authority. The read-only consumer at
`ops/macos/shopping/secret_preflight.py` validates the contract structurally,
resolves required names by action, and evaluates presence only. It never
inspects or serializes values. Unsupported actions, unknown supplied names,
invalid contract structure, and missing required names fail closed;
not-evaluated remains distinct from pass or fail.

Only the Secret Contract and Secret Preflight layers exist. No Secret Backend
has been selected or implemented, including SOPS, age, or Keychain; Secret
Materialization and Authorization / Mutation are also absent. The preflight
grants no authorization and performs no mutation, Keychain query, secret
materialization, or Docker, Colima, runtime, Caddy, WordPress, WooCommerce,
MariaDB, or Ubuntu access. Compose intentionally retains plain
`${SHOPPING_*}` interpolation so read-only runtime observation remains
secret-independent.

The desired WordPress binding remains
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80` with desired port `58082`; MariaDB
remains unpublished. Shopping service and WooCommerce capability status remain
`NOT_DEPLOYED`, and `SHOPPING_RUNTIME_ACTIVATED=false`. SM-01A performed no
Production activation or port cutover and consumed no Production
authorization. See
[SM-01 Secret Management](docs/architecture/SM-01-SECRET-MANAGEMENT.md).
Next: `SM-01B — Secret Delivery Backend v1`.

## PA-04 — Notification Platform v1

Status after Git closeout: `NOTIFICATION_PLATFORM_V1_VALIDATED`; PA-04 is
validated and closed. AIControlCenter owns notification intent, routing policy,
provider selection, governance, authorization, audit, retry policy, and the
future delivery lifecycle. External notification providers own transport
capability only. n8n, OpenClaw, WordPress, providers, and Ubuntu own neither
platform-wide notification business logic nor Production authorization.

`core.notifications` is the provider-neutral domain/platform boundary;
`integrations.notifications` contains replaceable observation-only provider
adapters; and `ops.macos.runtime.application` is the outer composition root.
Core imports neither `ops.*` nor `integrations.*`
(`CORE_OPS_IMPORT_COUNT=0`, `CORE_INTEGRATIONS_IMPORT_COUNT=0`). Provider and
routing statuses are separate: provider statuses are `AVAILABLE`,
`UNAVAILABLE`, `NOT_CONFIGURED`, `NOT_DEPLOYED`, `DEGRADED`, and `UNKNOWN`;
routing statuses are `PLANNED` and `BLOCKED`. V1 defines no actual delivery
lifecycle because provider execution is not implemented.

Observations normalize fail-closed. Only explicitly `AVAILABLE`,
`configured=true`, `available=true` providers are routable; malformed,
contradictory, exception-producing, mismatched, duplicate, or invalid providers
are not. Identities are bounded by `^[a-z0-9][a-z0-9._-]{0,63}$`; invalid
identities are never echoed and become literal `UNKNOWN`. Telegram is the known
reference provider: canonical truth is optional and `NOT_DEPLOYED`, while
configuration/readiness remain unknown unless explicitly observed. `DEPLOYED`
or `PRODUCTION` alone proves no availability, and no environment, credential,
endpoint, host, port, authentication, or network convention is inferred.

`core.capabilities.manifest` is the narrow shared canonical metadata lookup. It
validates its Draft 2020-12 schema and the manifest, requires exactly one
requested `service_id`, and fails closed for all invalid or unreadable input.
OpenClaw and n8n reuse it without changing PA-02/PA-03 outward behavior; it is
not a second `ServiceTopology` or lifecycle framework.

The exact new API is `GET /api/notifications/platform` and
`GET /api/notifications/providers`. It contains no action route, delivery,
retry, transport execution, Production authorization, or infrastructure
mutation. Existing `GET /notifications` and `POST /notifications` remain
unchanged and explicitly **LEGACY / OUTSIDE PA-04 SCOPE**; PA-04 does not call,
wrap, expand, authorize, or depend on them. Migration/deprecation is future,
separately governed work.

Final exact-code focused validation passed 85 tests after identity hardening;
the canonical regression passed `RC=0` on exactly one PA-04 invocation; and
`git diff --check` passed. No Production mutation, Production notification,
external provider I/O, or PA-04 execution occurred. Legacy POST was exercised
only by TestClient compatibility tests. No launchd, Docker, `runtime/current`,
credential, Caddy, WordPress, Ubuntu, or live-provider mutation occurred. No
Notion synchronization is claimed. OPS-01B and PA-01 through PA-03 remain
closed and unchanged. See
[`docs/architecture/PA-04-NOTIFICATION-PLATFORM.md`](docs/architecture/PA-04-NOTIFICATION-PLATFORM.md).

## PA-03 — n8n external automation capability boundary

Status after Git closeout: `N8N_CONTROL_PLANE_ADAPTER_V1_VALIDATED`; PA-03 is
closed. n8n is a replaceable external automation capability, not the
AIControlCenter Control Plane. AIControlCenter retains business logic, workflow
and orchestration policy, Production authorization, governance, audit,
deployment control, infrastructure mutation authority, and business/customer
state.

The final dependency direction is `ops.macos.runtime.application` →
`integrations.n8n` → `core.capabilities`, with dependency injection into
`core.api.create_app`. Core imports neither `ops.*` nor `integrations.*`.
Existing `core.capabilities` contracts and `CapabilityStatusService` are reused;
there is no second capability framework. Platform-neutral `create_app`
performs no n8n discovery and fails closed with value-free `UNAVAILABLE`
evidence when no adapter is injected. macOS outer application composition
injects the n8n adapter and truthfully projects `NOT_DEPLOYED`.

Canonical manifest/schema validation occurs before the unique n8n identity is
trusted. Current canonical truth is optional, `NOT_DEPLOYED`,
`runtime_health=false`, `runtime=UNASSIGNED`, and `supervisor=UNASSIGNED`. No
sufficiently proven executable, lifecycle, log, or runtime identity exists;
therefore PA-03 adds no PA-01 `service_platform` lifecycle definition.
Configuration, authentication, runtime, and transport remain `UNKNOWN` unless
explicitly injected as evidence. Implementation uses no invented n8n endpoint,
environment, or authentication convention.

The only PA-03 v1 API projection is `GET /api/capabilities/n8n`; no
POST/PUT/PATCH/DELETE capability implementation exists. PA-03 provides no
workflow execution, workflow enable/disable, webhook creation, credential
creation, schedule mutation, Production authorization, or infrastructure
mutation. Secret/config evidence is value-free: URLs, API keys, tokens,
cookies, headers, webhook secrets, environment values, configuration contents,
and exception messages are not projected. Shared governance explicitly states
`platform_business_policy_ownership=false` for external capabilities, and
PA-02 OpenClaw remains compatible.

Focused PA-03 validation passed 96 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-03 canonical invocation, and
`git diff --check` passed. No Production mutation or n8n workflow, credential,
Docker, launchd, `runtime/current`, or live-service operation occurred. No
Notion synchronization is claimed. OPS-01B, PA-01, and PA-02 remain closed and
unchanged.

## PA-02 — OpenClaw external capability boundary

Status after Git closeout: `OPENCLAW_ADAPTER_V1_VALIDATED`; PA-02 is closed.
OpenClaw is an optional, replaceable external capability, not a Control Plane.
AIControlCenter retains business logic, governance, Production authorization,
deployment control, workflow policy, infrastructure mutation authority, audit,
and business/customer state.

The final dependency direction is
`ops.macos.runtime.application` → `integrations.openclaw` →
`core.capabilities`, with the macOS outer composition injecting the adapter into
`core.api.create_app`. Core imports neither `ops.*` nor `integrations.*`.
Platform-neutral `create_app` performs no OpenClaw discovery and, without an
injected adapter, fails closed with value-free `UNAVAILABLE` evidence. The
macOS outer composition injects the adapter and truthfully projects
`NOT_DEPLOYED` from the schema-validated canonical manifest.

The canonical manifest identifies exactly one OpenClaw entry as optional,
`NOT_DEPLOYED`, and `runtime_health=false`; it is schema-validated before that
unique entry is trusted. No trustworthy launchd, runtime, or Service Platform
identity is proven, so PA-02 adds no `service_platform` lifecycle definition.
Endpoint, authentication, transport, and runtime identity remain
`UNKNOWN`/unproven by default. The implementation uses no `OPENCLAW_ENDPOINT`
or `OPENCLAW_API_KEY` convention.

The only API surface is `GET /api/capabilities/openclaw`; no
POST/PUT/PATCH/DELETE capability implementation exists. PA-02 v1 provides no
prompt forwarding, tool/action execution, lifecycle execution, Production
authorization, or infrastructure mutation. Secret/config evidence is
value-free: no endpoint URL, key, token, cookie, header, environment value,
credential value, or exception message is projected.

Focused PA-02 validation passed 79 tests. The canonical deployment regression
passed with `RC=0` on exactly one PA-02 canonical invocation, and
`git diff --check` passed. No Production mutation or additional deployment,
`launchctl`, `runtime/current`, credential, or live-service operation occurred.
No Notion synchronization is claimed. PA-01 and OPS-01B remain closed and
unchanged; WordPress and unrelated Shadow maintenance remain separate future
work.

## PA-01 — Control Plane Service Platform v1

Status after Git closeout: `CONTROL_PLANE_SERVICE_PLATFORM_V1_VALIDATED`;
PA-01 is closed.

PA-01 introduced Control Plane Service Platform v1. The canonical service
manifest is the service-definition source of truth, and `ServiceDefinition` is
a pure core service-level contract. `ServiceHealth` remains the sole owner of
aggregate runtime health, and `core` has zero direct `ops.*` imports.

The macOS outer composition is `ops/macos/runtime/service_platform.py`. Its
`inspect_platform_services()` composes `ServiceTopology.platform_services()`,
existing `ServiceHealth` launchd and heartbeat observation, strict filesystem
readiness, and immutable runtime/source validation. Filesystem contracts use
stable owner/group names resolved only at the macOS boundary. Exact file type,
symlink, mode, owner, and group validation remains fail-closed. Only `ENOENT`
is missing; other filesystem or identity inspection errors fail closed with
value-free evidence.

Canonical immutable `runtime/current` and Source validation reuses the existing
authoritative immutable-source validator and does not execute Production
worktree code. PA-01 lifecycle capability remains inspect-only. Dry-run may
describe bootstrap as planning metadata only, eligible only for `NOT_DEPLOYED`
with trusted launchd observation, ready filesystem, and immutable runtime/source
preconditions. It includes no authorization and performs no mutation, retry,
rollback, or kickstart.

Application Scheduler and canonical API were reference services without
changes to validated Production lifecycle behavior. The canonical API
entrypoint remains `ops.macos.runtime.application:app`; Shadow remains separate.
Final focused validation passed 94 tests under umask `077`. The final candidate
passed the canonical deployment regression with `RC=0` on exactly one canonical
invocation. `git diff --check` passed. No Production mutation occurred. No
Notion synchronization is claimed. WordPress and Shadow maintenance remains
deferred and separate.

## Immutable Production Source and canonical process recovery invariants

The Mac mini M4 remains the always-on Brain and sole Control Plane. Host Caddy
is the only public edge. WordPress is the CMS Engine, WooCommerce is the
Commerce Engine, and Ubuntu is an optional stateless infrastructure worker; it
owns no AI workload, application or business state, governance, authorization,
audit, deployment control, or Control Plane authority.

An active Production release is a paired identity:

- `runtime/venvs/<runtime-id>` contains the dependency Runtime.
- `runtime/sources/<runtime-id>` contains immutable tracked application Source.
- `runtime/current` selects the Runtime ID, and Runtime, Source, and approved
  full commit must agree exactly.

Immutable Source validation rejects both writable filesystem objects and
generated Python bytecode contamination, including `__pycache__`, `*.pyc`, and
`*.pyo`. Privileged Python executors that import project-local sibling modules
must set `sys.dont_write_bytecode = True` before those imports; environment
variables are defense in depth, not the sole protection. A contaminated
immutable release is retired and replaced by a newly built and independently
validated release. It is never repaired in place.

Production lifecycle control preserves strict read, plan, authorization, and
apply boundaries. One human authorization maps to one bounded mutation
invocation. Successful mutation followed by wrapper or observation failure
transitions to read-only reconciliation; it grants neither automatic retry nor
automatic rollback. Duplicate requests fail closed before authorization and
mutation if observed state no longer satisfies the expected precondition.
Authorization read inside a heredoc uses `/dev/tty`; expected-absence probes
must be safe under `set -e` and `pipefail`; generated wrapper redirections must
remain atomic; and JSON gates validate the actual emitted versioned schema.

Runtime health consumes `config/services/mac-standalone-production.json` as its
single service-topology contract. Logical identity, required/optional policy,
lifecycle, deployment state, and launchd labels are defined there; inspection
adapters only observe the lifecycle identifiers supplied by that contract.
Malformed topology fails closed. Runtime-health and scheduler-heartbeat reads
must not create, migrate, or update persistent state.

Endpoint-local success is not equivalent to whole-runtime health. A recovered
canonical API/Homepage may be operational while `/runtime/health` truthfully
reports degraded dependencies or stale heartbeats. Operational status must
preserve that distinction and must not promote HTTP status alone into a
platform-health claim.

## SHOP-AI-01A ProductDraft generation foundation

Status: `SHOP-AI-01A_PRODUCT_DRAFT_GENERATION_FOUNDATION_READY` at verified
implementation HEAD `52db3600ae76c70926e27ce930be70fe34f98452`.

`core/shopping/` remains the canonical Shopping domain and the existing SHOP-02
`ProductDraft`, `ProposedFields`, and immutable `ProductDraftRevision` model are
reused rather than replaced. The Shopping-owned structured generation contract
is version `1.0.0`. Generated fields carry AI `SuggestionProvenance`; the
candidate revision remains `LifecycleState.DRAFT` and causes no automatic
validation, human approval, or deployment intent.

The adapter reuses the canonical `core.providers.ProviderAdapter` with one
injected provider, `RetryPolicy(max_attempts=1)`, a bounded timeout, and no
provider fallback. Source context is canonicalized and snapshotted, and the
provider request ID remains traceable. The operation key is consumed before
provider invocation, providing **AT-MOST-ONE provider invocation per consumed
operation key within the injected coordinator's durability scope** and
concurrent duplicate suppression. This is not global exactly-once semantics.
The current `InMemoryProductDraftGenerationOperationCoordinator` is
non-production.

No durable ProductDraft persistence, durable operation ledger, transactional
revision/audit/operation Unit of Work, generation API, Dashboard mutation,
recommendation or ranking engine, WooCommerce write integration, Production
mutation authority, automatic retry, or automatic rollback was added. See
[`SHOP-AI-01A architecture`](docs/architecture/SHOP-AI-01A-PRODUCT-DRAFT-GENERATION-FOUNDATION.md).
Next: `SHOP-AI-01B_DURABLE_PRODUCT_DRAFT_GENERATION_TRANSACTION`.

## SHOP-01A reconciled Shopping baseline

SHOP-01A is retrospective baseline hardening over the existing SHOP-01/02/03
chronology. The canonical domain remains `core/shopping/`. At SHOP-01A1 HEAD
`f95ba9ae2133b55db06c362df321b16785f21423`, `/shopping` and the Shopping
dashboard share `build_default_shopping_service()`. The API is GET-only; one
read invocation permits one outbound HTTP GET attempt and automatic retry is
disabled.

The Mac mini M4 is the always-on Brain and AIControlCenter the single Control
Plane. WordPress is CMS/presentation, WooCommerce is the Commerce Engine, and
Ubuntu is a stateless infrastructure Worker with no Shopping business logic.
Production mutation authority is disabled. The intercepted
`WooCommerceControlledWriteAdapter` is retained library code, but no concrete
Production write transport, Production credential provider, runtime/API
wiring, or mutation endpoint exists. See the
[`SHOP-01A2 reconciliation`](docs/architecture/SHOP-01A2-REPOSITORY-UTILIZATION-AND-ARCHITECTURE-RECONCILIATION.md).

## SEC-02 Governance Control Plane

Status: `SEC-02A_GOVERNANCE_CONTROL_PLANE_ARCHITECTURE_READY`

The A0-A10 architecture phase is complete. Authorization follows only
`REQUESTED -> AUTHORIZED`, `REQUESTED -> REJECTED`, `AUTHORIZED -> STALE`, or
`AUTHORIZED -> CONSUMED`; `STALE`, `CONSUMED`, and `REJECTED` are terminal and
non-reusable. Current preconditions must `MATCH` before invocation permission.
Consumption is separate from invocation, and one orchestration permission
represents one bounded invocation. Remaining mutation budget is accounting
only, never retry authority.

`FAILED`, `UNCERTAIN`, `DRIFT`, failed postcondition, or failure evidence
produces `STOP`. There is no automatic retry or automatic rollback. Adapters
cannot authorize, widen scope or budget, retry, or roll back. Governance API
and dashboard projection is READ ONLY. See
[`docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md`](docs/architecture/SEC-02A10-ARCHITECTURE-CLOSURE.md).

SEC-02 freezes a reusable governance boundary under
`core/governance/control_plane/`, with pure domain rules, application-owned
orchestration and ports, bounded adapters, and a versioned contract family.
The canonical architecture is
[`docs/architecture/SEC-02-GOVERNANCE-CONTROL-PLANE.md`](docs/architecture/SEC-02-GOVERNANCE-CONTROL-PLANE.md),
the v1 semantic catalog is
[`docs/contracts/SEC-02-GOVERNANCE-JSON-V1.md`](docs/contracts/SEC-02-GOVERNANCE-JSON-V1.md),
and operator safety policy is
[`docs/operations/SEC-02-CONTROLLED-MUTATION-POLICY.md`](docs/operations/SEC-02-CONTROLLED-MUTATION-POLICY.md).

The Mac mini M4 remains the always-on Brain and AIControlCenter the sole Control
Plane. Ubuntu remains an optional stateless infrastructure Worker using bounded
JSON APIs; it owns no AI workload, business logic, application/governance/replay
state, authorization, or audit authority. SEC-02 creates no generic remote
command path. Existing deployment, governance-operations, and shopping domains
retain their business ownership and are wrapped through ports where useful.

SEC-02A is not a Production mutation implementation. No concrete Production
mutation adapter was implemented. Production mutation remains separately
human-authorized.

## AI provider boundary

AIControlCenter owns provider governance, routing, policy and normalization.
Business logic selects an explicit provider through `ProviderRouter` and talks
only to the replaceable `ProviderAdapter` contract; vendor SDK behavior belongs
behind adapters. Unknown and duplicate providers fail closed, retries are
bounded, and cross-provider fallback is prohibited. Credentials are external
secrets and API keys never belong in Git.

AI-PROVIDER-01A adds only a no-network OpenAI boundary and deterministic fake
adapter. AI-PROVIDER-01B is reserved for separately authorized credential
installation and authenticated connectivity. Production Runtime `7b171f135dc7`
and PI-009 authorization remain unchanged. Notion sync is `PENDING`. The
canonical decision is `docs/architecture/AI-PROVIDER-ADAPTER-ARCHITECTURE.md`.

AI-PROVIDER-01C-A integrates the existing canonical `BrainAgent.ask` workflow:
`BrainAgent -> ProviderRouter -> ProviderAdapter -> provider implementation`.
Provider selection is explicit from the request or configured Control Plane
policy. Business logic owns no vendor transport behavior, vendor objects cannot
cross the adapter boundary, unknown providers fail closed, and no automatic
cross-provider fallback occurs. This is repository-only; no authenticated call
or Runtime change occurred. 01C-B creates a Candidate Runtime and 01C-C requires
explicit human Production-promotion authorization. Notion is
`DEFERRED_UNTIL_FINAL_PHASE`.

<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:START -->
## ACTIVATION-01C Controlled Pointer Activation

Status: `COMPLETE`

Authorized transition:

`b9ad351a7241 -> acd80ab9f6ae`

Runtime pointer activation:

`PASS`

Activation report SHA-256:

`d59a3aa81accca4e6f330c85774924221e33e247376a069a1d922f5716dec24a`

Natural launchd KeepAlive recovery:

`PASS`

Explicit service restart commands:

`0`

Launchd state:

`running`

Listener:

`127.0.0.1:18100`

Listener/PID correlation:

`PASS`

Approved wrapper SHA-256:

`a58d926f8845f6b0aa7863250b02c0c461ea843bfa03a83313eaaa547ca98212`

Wrapper serving target:

`core.api.shadow:app`

HTTP validation:

- `GET /health -> 200`
- `GET /runtime/health -> 200`
- `POST /health -> 405`

Post-activation ACTIVATION-01B inspection ID:

`activation-inspection-bc8f2b34d45242c4b835d4ba852667a3`

Post-activation report digest:

`sha256:f419242b927804a6c97ad947ad4eb2deb9b2a07545724d750fd85ab3a80def22`

01B terminal status:

`BLOCKED`

Remaining transition-phase blockers:

`["GIT_IDENTITY_MATCH","GIT_VALIDATION_COMPLETE","PROCESS_SERVING_TARGET_MATCH","RUNTIME_CURRENT_MATCH"]`

Operational Runtime, launchd, listener and HTTP checks passed.

The residual blockers are contract-phase mismatches:

- pre-activation Runtime expectation
- Control Plane Git identity versus Candidate source identity
- launchd wrapper indirection versus direct serving-target inference

01C independently verifies the exact approved wrapper SHA and its
static `uvicorn core.api.shadow:app` exec chain.

Rollback executions:

`0`

Explicit launchd mutation commands:

`0`

Caddy changes:

`0`

Public openings:

`0`

Ubuntu changes:

`0`

Production authorization:

`NO`

ACTIVATION-01C does not constitute PI-009 Production authorization.
<!-- AICONTROLCENTER:ACTIVATION_01C_POINTER_CLOSEOUT:END -->

<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:START -->
## ACTIVATION-01C Authorization Contract

Status: `FROZEN`

Active Runtime: `b9ad351a7241`

Candidate Runtime: `acd80ab9f6ae`

Candidate source commit: `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`

Candidate startup import gate: `PASS`

Observed Active Runtime failure:

`ModuleNotFoundError: No module named 'jsonschema'`

First mutation boundary:

`Runtime pointer activation only`

Explicit service restart authority:

`NO`

Automatic rollback authority:

`NO`

Ubuntu changes:

`NO`

Public opening:

`NO`

Production authorization:

`NO`

Canonical human approval statement:

`ACTIVATION-01C AUTHORIZE POINTER SWITCH acd80ab9f6ae FROM b9ad351a7241`

The exact mutation command and rollback boundary are defined in:

- `docs/deployment/ACTIVATION-01C-CONTROLLED-ACTIVATION-ARCHITECTURE.md`
- `docs/operations/macos/ACTIVATION-01C-HUMAN-AUTHORIZATION-CONTRACT.md`
<!-- AICONTROLCENTER:ACTIVATION_01C_AUTHORIZATION_FREEZE:END -->

## Canonical Runtime serving-target authority

The two canonical macOS launchd runners,
`ops/macos/launchd/run-shadow-api.sh` and
`ops/macos/launchd/run-shadow-daemon.sh`, are the serving-target authority.
Both runners must declare exactly one complete target and must agree on the
same value. The canonical production serving target is
`core.api.shadow:app`. The Shadow application composes the internal FastAPI
application exposed as `core.api.app:app`; that internal target is
diagnostic/composition-only and must never be selected as the direct
production serving target.

Runtime Contract discovery fails closed when either canonical launcher is
missing, conflicting, declares multiple targets, or provides a malformed or
abbreviated target. Only unanimous agreement on one complete launcher target
can produce a selected serving target. Health endpoint discovery retains only
valid path-shaped endpoints, removes duplicates, and emits deterministic
output. This discovery contract is read-only and grants no build, activation,
restart, launchd or Caddy mutation, public opening, Ubuntu change, production
write, or production authorization; production remains `NOT_AUTHORIZED`.

## RUNTIME-BUILD-04A release and source boundary

Source/documentation commit
`acd80ab9f6aeb848900e1a19e3fa3afd69face8a` produced side-by-side release
`acd80ab9f6ae`. Each finalized release owns its Python interpreter and installed
dependencies, so dependency releases are immutable and can coexist. The build
and validation completed without changing `runtime/current`, which remained on
active Runtime `b9ad351a7241`; the new release was not activated.

The canonical serving target is `core.api.shadow:app`. The Shadow application
is `ReadOnlyASGI` and composes the internal FastAPI application
`core.api.app:app`. Direct localhost shadow smoke ran from the new release and
confirmed HTTP 200 for `/health`, `/runtime/health`, `/homepage/status`,
`/homepage`, `/homepage/product-management`, and `/datacenter/status`, plus HTTP
405 for `POST /health`. Exact smoke PID cleanup and listener cleanup passed.

The current immutability boundary is narrower than a fully source-immutable
application release: Python and dependencies are release-owned, but application
source is loaded from the mutable repository through `PYTHONPATH`.
`source_bundled_inside_release` is false and `repository_source_binding` is
true. Source bundling, a source manifest, and source-independent launch remain
future architecture work.

The builder emitted a valid structured JSON report on stdout. The host wrapper
found no canonical build-report JSON file, so the report was recovered and
validated from the builder log. That persistence mismatch is operational
tooling debt, not a release failure. An unavailable optional host `rg` command
was likewise not a release defect.

This release evidence does not grant activation authority. Runtime activation,
rollback execution, service restart, public staging, production, and production
writes remain `NOT_AUTHORIZED`. No service, launchd, Caddy, Ubuntu, public, or
production change occurred. The Mac mini M4 remains the sole Control Plane;
Ubuntu remains an optional stateless infrastructure worker with no AI workload,
business logic, application state, or Control Plane authority.

## Verified test, Git identity, and immutable Runtime boundaries

The Mac mini M4 remains the always-on Brain and sole Control Plane; Ubuntu
remains an optional stateless infrastructure worker and owns no AI workload,
business logic, application state, or Control Plane authority.

Controlled bootstrap validation receives identities, authorization, permit,
and claim identifiers and digests only through an immutable
`TrustedBootstrapEvidenceBinding`. Missing, incomplete, inconsistent, or
self-asserted-only binding evidence fails closed. The
`ControlledBootstrapEvidenceGenerator` deterministically emits the exact
canonical 14-artifact non-production evidence set, and operational snapshots
consume the public `ControlledMacBootstrapExecutor` contracts. Historical
retained host evidence and fixed historical identities are not test
dependencies; writable test state is confined beneath `/private/tmp` with
restrictive permissions.

Repository identity observation is deterministic, file-backed, and strictly
read-only. Exact loose refs take precedence over exact `packed-refs` fallback;
detached full object IDs are supported, while symbolic resolution is bounded
and cycle-detected. Unsafe, malformed, abbreviated, missing, or ambiguous refs
fail closed. This boundary executes no subprocess and writes no Git metadata,
and inventory responses retain the sanitized error boundary.

Every new immutable Runtime release must atomically publish both
`metadata.json` and a valid lowercase full-SHA
`.aicontrolcenter-source-commit` marker before activation. Existing immutable
releases must never be patched in place, and installed services must never
reference the mutable repository `.venv`. A separately authorized new release
must be built and validated before an atomic `runtime/current` switch. These
contracts grant no Runtime build or activation, public access, or production
write authority; production remains `NOT_AUTHORIZED`.

## R4 strict-live compatibility boundary

The strict preflight reader alone permits the exact required governance field
`ubuntu_participation`, and only when its value is Boolean `false`. Its exact
schema still rejects every unknown host, command, destination, environment,
worker, nested Ubuntu, or production field; the global unsafe-field policy is
unchanged. The live permit service returns the frozen
`ControlledLivePermitResult`, and the orchestrator type-checks and revalidates
Git, identity, time, one-use, digest, controlled scope, and production denial
before canonical serialization. No Ubuntu or runtime dependency was added.

## Recovery-2 evidence boundary

Only `core.deployment.git_readonly_evidence` may import subprocess for the
deployment-control Git capability. It uses fixed `/usr/bin/git` read commands,
exact cwd, minimal environment, bounded timeout/output, and no shell, write,
credential, hook, or network command. The live package consumes its typed
collector/validator and does not import subprocess. Existing public SQLite
inspectors and PRE_ACTIVATION monitoring remain independent evidence
authorities; post-claim failures preserve canonical mode-0600 evidence.

## Controlled operational composition boundary

`core.deployment.operational_bootstrap_live` is the only reviewed local live
composition boundary. It invokes the existing execution coordinator directly;
earlier packages do not import it, and it exposes no API, worker, remote
command, or network surface.
The recovery composition fixes concrete readers, authorization, permit, atomic
claim, trusted `pwd` home, host/path validation, Mac runtime, evidence writer,
and execution coordinator collaborators. Callers cannot select collaborators
through JSON, CLI, or environment. The validation runner remains
validation-only.

## Operational permit issuance review boundary

M3-A4B2B1A is a pure Mac Control Plane review package binding existing M3-A4
evidence by canonical digest. It has no adapter, persistence, executor, network,
API or worker dependency and grants no authorization. Ubuntu cannot authorize,
issue, claim or execute a permit. Production remains NOT_AUTHORIZED.

## M3-A4B2B0 Read-Only Host Preflight Boundary

`core.deployment.operational_bootstrap_preflight` is a Mac Control Plane-owned,
read-only evidence and deterministic policy boundary. It validates the Darwin
host, exact Git/test/safety state, absent future targets, filesystem locality,
capacity, permission feasibility and closed-track evidence without a clock,
write adapter, database writer, executor, permit registry, subprocess, network,
API, worker or Ubuntu dependency. M3-A4B2B0 is closed; no permit,
authorization, bootstrap, target creation or Production activation occurred.
Next: M3-A4B2B1 Operational Permit Issuance.

## M3-A4B2A Controlled Bootstrap Validation Boundary

`core.deployment.operational_bootstrap` is the Mac Control Plane-owned
standard-library boundary for `TEST_ONLY_BOOTSTRAP_VALIDATION`. It is confined
to an exact injected pytest root under `/private/tmp` and has no API, worker,
Ubuntu, subprocess, network, writer composition or dispatch dependency.
M3-A4B2A is closed after single-use permit, schema, baseline recovery,
pre-activation evidence and cleanup validation. Operational execution remains
absent and Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2B.

## M3-A4B1 Controlled Bootstrap Authorization Boundary

`core.deployment.operational_bootstrap_authorization` is a pure, deterministic
Mac Control Plane authorization boundary over public M3-A4A readiness
contracts. It binds exact Git, readiness, restriction, target, schema, plan,
safety, identity, approval, and validity evidence into a canonical one-use
controlled-non-production permit. Only an injected registry protocol exists;
there is no persistence or bootstrap executor. M3-A4B1 is closed after
synthetic validation. No operational permit was issued, no bootstrap was
authorized or executed, operational paths remain absent, writers remain
inactive, and Production activation is `NOT_AUTHORIZED`. Next: M3-A4B2.

## M3-A4A Operational Activation Readiness Boundary

`core.deployment.operational_activation_gate` is a collision-free, pure,
immutable and evidence-only Mac Control Plane boundary. It validates closure,
test, Git, safety, recovery, monitoring, future path/permission, bootstrap and
rollback evidence without clocks, probes, persistence, commands, network,
executors, API, worker or Ubuntu dependencies. Its readiness result is not an
authorization. M2, M3-A1, M3-A2, M3-A3 and M3-A4A are closed; operational
databases remain uncreated, writers and monitoring remain inactive, external
dispatch remains unimplemented, bootstrap authorization is not granted and
Production activation is `NOT_AUTHORIZED`. Next: M3-A4B Controlled Mac
Operational Bootstrap.

## M3-A3C Monitoring and Alert Drill Boundary

`core.deployment.monitoring_alert_drill` consumes only public M3-A3A and M3-A3B
contracts. It deterministically validates the complete monitoring-to-routing
flow and simulates logical receipts in an injected object-scoped sink. It has
no filesystem, database, network, subprocess, API, worker, Ubuntu, external
adapter, or production composition dependency. M3-A3C and the M3-A3 track are
closed. External dispatch and persistence remain unimplemented; operational
monitoring remains inactive and Production activation is `NOT_AUTHORIZED`.
Next: M3-A4 Controlled Operational Activation Gate.

## M3-A3B Alert Routing Boundary

`core.deployment.alert_routing` is a collision-free pure policy package owned
by AIControlCenter on the Mac Control Plane. It consumes only immutable M3-A3A
public contracts, explicit configuration, history, snapshot binding and
timestamps. It deterministically returns logical routes, suppression and
escalation decisions without dispatch, persistence, acknowledgement, clock,
database, command, network, API, worker or Ubuntu dependencies. M3-A1, M3-A2,
M3-A3A and M3-A3B are closed. Operational monitoring remains inactive,
operational databases remain uncreated and Production activation is
`NOT_AUTHORIZED`. M3-A3C Monitoring and Alert Operational Drill is next.

## M3-A3A Operational Monitoring Boundary

`core.deployment.operational_monitoring` is the pure, read-only monitoring
authority owned by AIControlCenter on the Mac Control Plane. It consumes
immutable public evidence, explicit timestamps and explicit thresholds and
returns deterministic PRE_ACTIVATION snapshots plus alert candidates. It has
no clock, persistence, database, adapter, command, network, notification,
API-worker or Ubuntu dependency. Alert dispatch and monitoring persistence are
not implemented. M3-A1, M3-A2 and M3-A3A are closed; operational databases and
writers remain inactive and Production activation is `NOT_AUTHORIZED`.

## M3-A2C Permit and Replay Recovery Boundary

The Mac Control Plane owns authoritative replay state. M3-A2A read-only
inspection remains intact, M3-A2B writing remains operationally disabled, and
M3-A2C adds separate explicit-path online backup, restore, exact recovery and
concurrency validation. Ubuntu owns no permit, nonce, replay, backup or
recovery state. All writable validation used pytest temporary paths. M3-A1 and
M3-A2A through M3-A2C are closed; no operational database, backup schedule,
restore or writer is active, and Production activation is `NOT_AUTHORIZED`.
M3-A3 Operational Monitoring and Alerts is next.

## M3-A1C SQLite Audit Recovery Boundary

`core.deployment.audit_sqlite_recovery` is a separate Mac Control Plane
boundary over M3-A1A inspection and M3-A1B schema contracts. Explicit-path
SQLite online backup, canonical manifest binding, separate-target restore and
deterministic recovery comparison are fail-closed and operationally disabled.
Ubuntu owns no authoritative backup or recovery state. M2 and M3-A1A through
M3-A1C are closed after pytest-only validation; no operational database,
backup schedule or restore exists, persistent writer activation is not
started, and Production activation is `NOT_AUTHORIZED`. M3-A2 is next.

## M3-A1B Append-Only SQLite Audit Writer Boundary

`core.deployment.audit_sqlite_writer` is a separate AIControlCenter-owned Mac
Control Plane adapter that appends canonical audit events to an explicitly
injected, pre-existing SQLite ledger. It cannot create, migrate or repair a
database and does not weaken `core.deployment.audit_sqlite`, which remains
read-only. WAL, schema, append-only triggers and the full hash chain are
validated before each serialized append. M2, M3-A1A and M3-A1B are closed.
Only pytest temporary databases were used; operational activation and
Production writes remain prohibited. M3-A1C is next.

## M2 Pilot Evidence and Rollback Boundary

`core.deployment.pilot_activation` and `pilot_evidence` are AIControlCenter-
owned Mac Control Plane boundaries. M2-P3 validates immutable activation
evidence and derives fixed rollback steps before an injected test-only port can
act. Production code has no filesystem rollback adapter. One controlled
activation and rollback ran only below pytest temporary roots; persistent host
activation is not started, persistent host rollback is not implemented and
Production activation remains `NOT_AUTHORIZED`.

## M2 Pilot Authorization Boundary

`core.deployment.pilot_authorization` is a pure AIControlCenter-owned policy
boundary on the Mac Control Plane. It composes public DPL-03C authorization,
DPL-04D readiness and typed executor contracts without importing an adapter,
API, worker, persistence, network or command implementation. Permits are
deterministic, one-use, non-production and exact-scope bound. They do not start
the pilot. Ubuntu owns no authorization or audit. Persistent SQLite audit is
not implemented and Production activation is `NOT_AUTHORIZED`.

## DPL Durable Audit Boundary

AIControlCenter owns authoritative durable deployment audit on the Mac Control
Plane. The audit domain is canonical JSON with stable IDs, deterministic
digests and tamper-evident hash-chain linkage behind a replaceable
`DurableAuditPort`. The selected future adapter is an append-only SQLite ledger
stored outside Git; SQLite is not the domain model and is not implemented in
DPL-04C. Ubuntu cannot own audit policy or state. Query integration is
read-only-first; retention, deletion, compaction and production activation are
not authorized.

## DPL Mac Sandbox Boundary

`core.deployment.sandbox_adapter` is a Mac Control Plane adapter implementing
the typed non-production executor port. It depends inward on DPL contracts and
ports only. Planning, authorization, GET-only API composition and workers
cannot import it. The adapter requires an injected non-repository sandbox root,
confines canonical JSON artifacts beneath it, and has no command, network,
runtime-service, Ubuntu or production capability. Missing-root composition is
deny-only, and evidence is not durably persisted.

## Platform Goal

AI Home Datacenter is a production-ready,
multi-year AI platform rather than a conventional
home server.

## Mac mini M4 — Control Plane

The Mac mini is the always-on Brain and the single
AIControlCenter Control Plane.

It owns:

- AI orchestration and agents
- business logic and workflow orchestration
- Dashboard and Homepage
- WordPress and WooCommerce headless integration
- n8n automation
- scheduling and notifications
- GitHub, Notion, and Ubuntu control
- AI product and customer workflows

## Ubuntu Server — Infrastructure Worker

Ubuntu is an on-demand, stateless infrastructure
worker.

It provides:

- Docker and container runtime
- storage and file operations
- Immich, Nextcloud, and Plex
- backups
- infrastructure JSON APIs

Ubuntu must not own AI workloads, business logic,
Control Plane orchestration, or application state.

## Architecture Principles

- Git First
- JSON First
- REST and headless architecture
- Docker Compose and Infrastructure as Code
- read-only monitoring before write operations
- stateless infrastructure workers
- modular services
- automated testing and documentation
- rollback before cutover

## Current Runtime Architecture

The Mac Shadow API is supervised by a system
LaunchDaemon.

- Service: system/com.aicontrolcenter.api.shadow
- Application user: kyouhan
- Listener: 127.0.0.1:18100
- Mode: shadow-read-only
- Runtime: commit-specific Python virtual environment
- GUI login required: false
- Mutating HTTP methods: blocked

## Production Gate

Ubuntu AIControlCenter remains active until:

- Headless Reboot Recovery passes
- 24-hour Shadow observation passes
- Ubuntu Worker JSON integration passes
- Cutover and rollback validation pass

<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:START -->
## ADR: Mac Control Plane Production Baseline

**Status:** Accepted and operationally verified.

The Mac mini M4 is the sole AIControlCenter
Control Plane.

Ubuntu remains a stateless infrastructure worker.

Runtime flow:

`system launchd`
→ `root-owned runner`
→ `non-root application user`
→ `commit-specific Python runtime`
→ `AIControlCenter Shadow API`
→ `127.0.0.1:18100`

Validated contracts:

- Repository commit: `1e102c001c28108bee9583294abee77ce7d43643`
- Runtime commit: `1e102c001c28`
- Health: HTTP `200`
- Write protection: HTTP `405`
- Listener: `127.0.0.1:18100`
- GUI login dependency: none
- Transactional install: enabled
- Transactional rollback: enabled
- launchd settle after bootout: 2 seconds
- Final restart PID: `19761 → 19842`

Ownership boundaries:

- Mac owns AI, orchestration, business logic,
  scheduling, workflow and application state.
- Ubuntu owns Docker, storage, backup and file
  operations only.
- Ubuntu must not own AI workloads, business
  logic, Control Plane orchestration or
  application state.
- Infrastructure is consumed through JSON APIs.
- Production writes remain disabled until a
  separate cutover Gate is approved.
<!-- AICONTROLCENTER:CONTROL_PLANE_BASELINE:END -->

## Dashboard Shadow Control Plane

The Mac mini is the AI Home Datacenter Control Plane.

AIControlCenter owns Control Plane status, policy, orchestration, authorization and runtime observability.

### Request Architecture

```text
Mac mini
  -> AIControlCenter Shadow API
  -> GET /dashboard
  -> DashboardAPI
  -> ControlPlaneStatus
  -> RuntimeMetadata
  -> immutable metadata.json
```

The Dashboard consumes normalized JSON. It does not parse human-readable shell output.

### Runtime Metadata Architecture

Each commit-specific Runtime contains an immutable metadata file:

```text
~/Library/Application Support/AIControlCenter/runtime/
  current
  venvs/
    <12-character-commit>/
      bin/python
      metadata.json
      .aicontrolcenter-source-commit
```

Runtime metadata schema version 1 contains:

- Full 40-character Git commit
- 12-character short commit
- Runtime mode
- UTC creation timestamp

The metadata provider validates:

- Supported schema version
- Full commit format
- Short commit consistency
- Supported Runtime mode
- Required timestamp

Invalid, missing or unreadable metadata is returned as normalized JSON with `available: false`.

Invalid metadata does not crash the Dashboard API.

The runtime identity contract consists of both `metadata.json` and
`.aicontrolcenter-source-commit`. The generator validates the full Git commit
as exactly 40 lowercase hexadecimal characters, then atomically publishes both
files before activation. The marker contains that commit followed by one
newline. Missing or invalid identity metadata fails closed. Existing immutable
releases are never repaired in place; a replacement runtime must be built from
committed Git source.

### Runtime Activation Gate

The canonical macOS Runtime builder has two explicit public modes and three
internal phases:

```text
--mode build
  Runtime Contract validation
  -> repository commit validation
  -> clean Git validation
  -> owned staging virtual environment
  -> dependency installation
  -> application import validation
  -> test suite
  -> metadata generation
  -> metadata schema validation
  -> atomic finalization as an immutable commit-specific release

--mode activate
  finalized release validation
  -> exact source-marker and metadata validation
  -> atomic runtime/current switch
```

Build mode cannot change `runtime/current`. Finalized releases are immutable;
an existing release fails closed and is never repaired or patched in place.
Activation is a distinct, explicit, independently authorized operation. An
invocation without a valid explicit mode fails closed, and the mutable
repository `.venv` is never an activation candidate.

Metadata or source-marker failure prevents finalization and activation. A
service restart is a further, separate operational gate and is performed by
neither mode. The Mac mini M4 remains the sole Control Plane. Ubuntu remains
an optional stateless infrastructure worker and owns no AI workload, business
logic, application state, or Control Plane authority. Production remains
`NOT_AUTHORIZED`.

### Safety Policy

The Shadow API is read-only.

Allowed methods:

- GET
- HEAD
- OPTIONS

Write requests are rejected with HTTP `405`.

Dashboard requests must not execute:

- Git commands
- `launchctl`
- Runtime symlink mutation
- Infrastructure write operations

Ubuntu remains a stateless infrastructure worker.

Ubuntu is not involved in Control Plane business logic or AI workloads.

<!-- AICONTROLCENTER:PI-002:START -->
## PI-002 Ubuntu Worker Health JSON Adapter

AIControlCenter monitors the Ubuntu infrastructure worker through a read-only JSON adapter.

Production execution path:

```text
system LaunchDaemon
→ canonical Mac runner
→ root-owned worker environment
→ production worker configuration
→ SSH transport adapter
→ Ubuntu worker health JSON script
→ MonitoringSnapshot
→ Dashboard JSON
```

Production contracts:

- Mac mini remains the Control Plane.
- Ubuntu remains a stateless infrastructure worker.
- Ubuntu does not own platform business logic or application state.
- Worker integrations are read-only.
- Worker transport is bounded by connection and command timeouts.
- Worker failures return structured optional-error JSON.
- Worker failure does not make the Control Plane API unavailable.
- `GET /dashboard` monitors `ubuntu-main` by default.

Runtime configuration:

- Supervisor: `system/com.aicontrolcenter.api.shadow`
- Runtime user and group: `kyouhan:staff`
- Worker environment: `/Library/Application Support/AIControlCenter/worker.env`
- Worker environment ownership and mode: `root:staff 640`
- Production worker config: `config/workers.mac-production.yaml`
- Local listener: `127.0.0.1:18100`

The worker environment contains configuration only. SSH private keys and passwords are not stored in it.
<!-- AICONTROLCENTER:PI-002:END -->

<!-- AICONTROLCENTER:PI-003:START -->
## PI-003 Ubuntu Worker Minimum Closure

The Mac mini Control Plane must remain fully operational when the Ubuntu worker is powered off or unavailable.

Architecture contract:

- Mac mini is the mandatory always-on Control Plane.
- Ubuntu is an optional on-demand infrastructure worker.
- Ubuntu does not own AI workloads, platform business logic or Control Plane state.
- Ubuntu unavailability must not interrupt AIControlCenter health or Dashboard availability.
- Worker failures are represented as structured optional JSON errors.
- Immich and Nextcloud are Ubuntu-local infrastructure services.
- Ubuntu-local containers recover through `docker.service` and `restart: unless-stopped`.

Validated standalone behavior:

- AIControlCenter remained `ONLINE` with Ubuntu powered off.
- `GET /health` returned HTTP `200`.
- `GET /dashboard` returned HTTP `200`.
- `ubuntu-main` returned `OPTIONAL_UNAVAILABLE`.
- The Control Plane continued operating without Ubuntu.
<!-- AICONTROLCENTER:PI-003:END -->

<!-- AICONTROLCENTER:PI-004:START -->
## PI-004 Mac Standalone Production Baseline

- Mac mini is the mandatory standalone Control Plane.
- Ubuntu is an optional infrastructure worker.
- AIControlCenter runs through a system LaunchDaemon.
- Production uses an immutable commit-specific Python runtime.
- Homepage is an embedded read-only API at `/homepage/status`.
- Homepage reuses the Dashboard optional-worker contract.
- Storage and backup are optional external-worker capabilities.
- Mac reboot recovery was validated without Ubuntu.
<!-- AICONTROLCENTER:PI-004:END -->

<!-- AICONTROLCENTER:PI-005:START -->
## PI-005 — Mac Service Deployment Platform

AIControlCenter owns Mac service deployment governance, validation, inspection, approval policy, and audit evidence.

The deployment pipeline is JSON-first and separates read-only operations from write operations:

`Manifest → Validate → Plan → Inspect → Diff → Dry-run → Approval → Future Executor`

Ollama is defined as a replaceable native macOS model runtime. It has no platform-wide business logic and has no Ubuntu dependency.

The canonical Ollama network contract is loopback-only at `127.0.0.1:11434`, with model inventory health at `/api/tags`.

PI-005 does not install Ollama, create a LaunchDaemon, download models, or enable deployment execution.
<!-- AICONTROLCENTER:PI-005:END -->

<!-- AICONTROLCENTER:PI-006:START -->
## PI-006 — Approved Ollama Native Deployment Complete

PI-006 established Ollama 0.32.1 as an approved native macOS runtime on the Mac mini M4 Control Plane.

Production baseline:

- AIControlCenter remains the single Control Plane.
- Ollama is a replaceable local model runtime and owns no platform business logic.
- Ubuntu remains a stateless infrastructure worker and runs no AI workloads.
- Ollama service: `system/com.aicontrolcenter.ollama`
- Ollama endpoint: `127.0.0.1:11434`
- AIControlCenter service: `system/com.aicontrolcenter.api.shadow`
- AIControlCenter endpoint: `127.0.0.1:18100`
- Read-only API: `GET /api/services/ollama`
- Production runtime: `3679588b760c`
- Rollback runtime: `7cb2e7a400a6`
- Model inventory: `0`
- AIControlCenter and Ollama listeners: loopback-only
- Operational gate: passed
- Git state at operational validation: clean

Validation:

- Full suite: 481 passed, 5 deselected, 423 warnings.
- AIControlCenter health: ONLINE.
- Ollama health: ONLINE.
- Runtime metadata gate: passed.
- Deployment summary validation code: 0.

Production evidence:

`~/Library/Application Support/AIControlCenter/runtime/evidence/pi-006/api-release-3679588b760c-20260720T235541Z`

Safety corrections completed during PI-006:

- Isolated mocked Ollama binary targets from `/opt/homebrew/bin/ollama`.
- Separated Homebrew user operations from privileged system operations.
- Restored and correctly registered the Ollama API router inside `create_app`.
- Distinguished the active system LaunchDaemon architecture from the legacy GUI LaunchAgent manager.
- Revalidated the final operational gate using a Python assertion after a pasted shell assertion was damaged.

Deferred technical debt:

- Replace deprecated `datetime.utcnow()` usage with timezone-aware UTC values.
- Resolve remaining Python, Starlette, and dependency deprecation warnings.
- Approve model acquisition, checksum, retention, resource, and removal policies before downloading a model.
<!-- AICONTROLCENTER:PI-006:END -->

<!-- AICONTROLCENTER:PI-007:START -->
## PI-007 — Approved Model Lifecycle Monitoring and Governance

AIControlCenter is the sole control plane and source of truth for model
approval, lifecycle policy, compliance evaluation, audit, and API exposure.

The model-governance flow is:

1. `config/model-governance.json` defines the approved registry.
2. `core/governance/model_registry.py` validates the registry using a
   default-deny, read-only contract.
3. Ollama provides observed local inventory only.
4. `core/governance/model_evaluator.py` compares approved and observed models.
5. `GET /api/governance/models` exposes the evaluation as JSON.

Supported compliance states include `COMPLIANT`, `UNAPPROVED`, `MISSING`,
`DIGEST_MISMATCH`, and `RESOURCE_POLICY_VIOLATION`.

Model pull, create, copy, and delete operations remain denied. Ollama does not
own platform governance or business logic. Ubuntu remains a stateless
infrastructure worker and must not run AI workloads, store AI models, or own
model-governance state.
<!-- AICONTROLCENTER:PI-007:END -->

## PI-008: Model Governance Audit and Dashboard Integration

PI-008 establishes a read-only model-governance audit subsystem owned by AIControlCenter.

### Ownership

AIControlCenter owns:

- canonical governance audit snapshot schema
- audit orchestration
- immutable snapshot identity
- SQLite audit persistence
- historical comparison
- read-only audit APIs
- Dashboard audit read model
- deployment provenance and runtime identity

Ollama provides observed model inventory only.

Ubuntu remains a stateless infrastructure worker and owns no AI workload, model state, audit application state, or platform business logic.

### Persistence

Audit state is stored on the Mac mini at:

`~/Library/Application Support/AIControlCenter/data/model-governance-audit.sqlite3`

The database is outside the runtime directory and uses:

- SQLite WAL mode
- schema versioning
- append-only snapshot storage
- update-denied triggers
- delete-denied triggers
- no automatic deletion
- no automatic compaction
- online backup only

### Read-only API

PI-008 exposes GET-only endpoints:

- `/api/governance/audit/latest`
- `/api/governance/audit/snapshots`
- `/api/governance/audit/snapshots/{snapshot_id}`
- `/api/governance/audit/comparison`

No model pull, create, copy, delete, remediation, or other write operations are permitted.

### Dashboard

`/dashboard` includes the `model_governance_audit` read model.

The Dashboard integration is fail-soft and exposes governance status without owning audit persistence or remediation logic.

### Runtime provenance

Production runtime identity is derived from immutable release metadata:

`.aicontrolcenter-source-commit`

The Production runner no longer depends on mutable Git HEAD or Git working-tree cleanliness.

Active Production release:

- source commit: `b9ad351a7241e521c8964218f59724fcb04db93c`
- runtime release: `b9ad351a7241`
- rollback release: `0352e396f329`

<!-- PI-009:START -->
## PI-009 — Governance Audit Operations Visibility

Status: **Implementation Complete / Production Activation Pending**

AIControlCenter owns governance audit operations policy, scheduling,
projection, API presentation, Dashboard composition and operational
authorization.

The implementation provides:

- an append-only governance operations domain and SQLite adapter;
- an application-layer operational projection;
- a strict GET-only read API;
- a panel-local fail-soft Dashboard projection;
- lowercase presentation vocabulary at the API boundary;
- no automatic migration, retry, restore or remediation;
- no Ubuntu business logic or application-state ownership.

The production database remained unchanged during implementation and
validation. Production migration and scheduler activation require the
separate PI-009 Production Activation Gate.
<!-- PI-009:END -->

<!-- PI-009-OPERATIONS-FINAL:BEGIN -->
## PI-009 Final Architecture Decision

Governance operation execution is separated from
scheduling policy.

    JSON CLI
      -> OperationsApplicationService
           -> SQLiteOperationsEventRepository
           -> SystemUTCClock
           -> AutomationExecutor
           -> BackupVerifyService

AIControlCenter owns composition, policy validation,
locking, JSON output and audit dispatch.

The runner does not own cadence, retry, catch-up,
remediation or restore policy. No governance business
logic is placed on Ubuntu.

External schedulers may invoke the one-shot interface
only after a separate controlled activation gate.
<!-- PI-009-OPERATIONS-FINAL:END -->

<!-- PI-010-HEADLESS-PRODUCTION-CLOSE-2026-07-23 -->
## PI-010 Headless Scheduler Architecture

AIControlCenter owns governance cadence, policy, execution, JSON output, audit correlation, authorization, and deployment control.

The managed user crontab is a replaceable Mac mini operating-system adapter. Governance run identity and scheduled time remain inside the application and audit boundary.

Dedicated parameterless capabilities implement governance audit snapshot generation and SQLite online backup verification. No governance scheduling, AI workload, application state, or business logic runs on Ubuntu.

<!-- BEGIN AICONTROLCENTER SPF-002 ARCHITECTURE -->
## Shopping Platform Foundation

Status: SPF-002 CLOSED

- Control Plane: AIControlCenter
- Package root: `core/shopping`
- WordPress role: Headless CMS only
- WooCommerce role: Replaceable commerce engine only
- Ubuntu role: Stateless infrastructure worker
- Sprint 1 mode: Read-only
- Shopping write operations: Disabled

WordPress and WooCommerce integrate through REST/JSON adapters.
Direct external database access is prohibited.
Governance, authorization, audit, workflow, and policy remain in AIControlCenter.

Canonical detail: `docs/architecture/shopping-platform-foundation.md`
<!-- END AICONTROLCENTER SPF-002 ARCHITECTURE -->

<!-- SPF-003:START -->
## SPF-003 — Shopping Read-Only Port Foundation

Status: **Closed** on 2026-07-23.

- `core.shopping` is the application-owned Shopping bounded context.
- Seven transport-neutral ports expose read-only or compute-only capabilities.
- `CommerceCatalogPort` remains compatible through the byte-preserving `ports.py` to `ports/__init__.py` migration.
- Provisional JSON-first contracts remain isolated in `core.shopping.contracts.provisional`.
- Commerce, CMS, webhook, snapshot-persistence, and audit-append writes remain disabled.
- Canonical contract freezing is assigned to **SPF-004 — Canonical JSON Schema v1**.

Implementation commit: `fd52aad1d9af9d056d80d8f7d6170605ea0d11b2`.
<!-- SPF-003:END -->


<!-- AICONTROLCENTER-SPF-004-CLOSED -->
## SPF-004 Canonical JSON Schema v1

Status: CLOSED

Shopping contracts now use a versioned, vendor-neutral canonical JSON contract layer owned by AIControlCenter.

- JSON Schema dialect: Draft 2020-12
- Contract schema version: `1.0.0`
- Canonical contract bindings: 15
- Schema resources: 17
- Registry asset: `core/shopping/contracts/schemas/v1/registry.json`
- Explicit loader: `core.shopping.contracts.schema_registry.load_schema_registry`
- Runtime validation: `Draft202012Validator`
- Unknown contracts fail closed.
- Unknown payload fields are rejected by canonical strict objects.
- Remote and network schema resolution are prohibited.
- Schema assets are not loaded automatically during module import.
- Vendor DTOs remain adapter-private.
- Shopping write operations remain disabled.

Canonical contract validation belongs to the Mac mini AIControlCenter Control Plane. Ubuntu remains a stateless infrastructure worker and does not own Shopping contracts, state, business logic, or validation policy.

Implementation commit: `7a436a62fbaa2c176e877297d88b810b255f2776`

<!-- SPF-005-CLOSE:BEGIN -->
## SPF-005 Capability Governance — CLOSED

AIControlCenter owns Shopping capability governance and read authorization orchestration.

- Capability registry is static, immutable, vendor-neutral, and controlled by AIControlCenter.
- Eleven Shopping READ capabilities are registered.
- Nine WRITE capability identifiers are reserved but are not executable.
- Unknown capabilities fail closed.
- WRITE capabilities fail closed before policy evaluation.
- Known READ capabilities require `PolicyDecisionPort.evaluate_read`.
- Request and decision capability mismatches fail closed.
- Policy evaluation exceptions are normalized to `shopping.policy.evaluation_error`.
- Raw vendor or adapter exception messages are not exposed through authorization denial.
- No adapter execution, production registration, Ubuntu business logic, or Shopping write operation was enabled by SPF-005.

Authorization flow:

`Capability Registry -> READ classification -> PolicyDecisionPort -> explicit allow -> authorized read`

Implementation commit: `f807cc0dfb8a27d2bf387bdc3dd897e4fe331953`

Validation baseline: 22 targeted tests passed; 775 full regression tests passed.

Next architecture task: SPF-006 Read Adapter Contracts.
<!-- SPF-005-CLOSE:END -->

<!-- SPF-006-CLOSE:BEGIN -->
## SPF-006 Read Adapter Contracts — CLOSED

AIControlCenter owns the authoritative Shopping read ports and adapter contract boundaries.

- `CommerceReadPort` remains the authoritative callable Commerce interface.
- `CmsReadPort` remains the authoritative callable CMS interface.
- Adapter contract modules validate exact async method conformance against those ports.
- Commerce canonical returns are `ProductSnapshot`, `ProductSnapshotPage`, and `OrderSummary`.
- CMS canonical returns are `ContentSnapshot` and `ContentSnapshotPage`.
- SPF-005 capability bindings remain authoritative and are consumed rather than duplicated.
- Commerce and CMS capability sets are isolated.
- Vendor DTO escape, adapter-owned business logic, adapter-owned policy evaluation, and WRITE methods are prohibited.
- No live WooCommerce or WordPress network connection is enabled by SPF-006.
- Live vendor integration and adapter health monitoring remain deferred to SPF-007.

Implementation commit: `fd1bbe2ff212e9eeb442562ffeed32bed97c1072`.

Validation baseline: 28 targeted tests passed; 803 full regression tests passed.

Next architecture task: SPF-007 Adapter Health Monitoring.
<!-- SPF-006-CLOSE:END -->

<!-- SPF-007-CLOSE:BEGIN -->
## SPF-007 Adapter Health Monitoring — CLOSED

AIControlCenter owns Shopping adapter health semantics, monitoring aggregation, routing signals, and operational governance.

- `AdapterHealthPort` remains the authoritative health read port.
- Health states are `HEALTHY`, `DEGRADED`, and `UNAVAILABLE`.
- Failure taxonomy is vendor-neutral and fail-closed.
- Timeout, transport, authentication, authorization, invalid payload, schema mismatch, dependency, configuration, and unknown failures resolve to unavailable health.
- Latency and rate-limit conditions resolve to degraded health.
- Health is not authorization and does not bypass SPF-005 capability or policy governance.
- Probe normalization rejects raw vendor error text and credential-bearing metadata.
- Health aggregation is deterministic and stateless.
- Overall precedence is `UNAVAILABLE > DEGRADED > HEALTHY`.
- Empty aggregation input resolves to `UNAVAILABLE`.
- Probe-layer retry, persistence, scheduler ownership, business writes, and adapter-owned policy decisions are prohibited.
- Live WooCommerce and WordPress transport remains disabled by SPF-007.
- Ubuntu remains a stateless infrastructure worker.

Implementation commit: `63263b734ead4eb083f9b91923f4b41c3b644e34`.

Validation baseline: 34 targeted tests passed; 837 full regression tests passed.

Next architecture task: SPF-008 Read-only Snapshots.
<!-- SPF-007-CLOSE:END -->

<!-- SPF-008-CLOSE:BEGIN -->
## SPF-008 Read-only Snapshots — CLOSED

AIControlCenter owns Shopping snapshot governance and read orchestration.

- `SnapshotRepositoryPort` remains the authoritative snapshot read boundary.
- Supported repository operations remain `get_latest_snapshot` and `list_snapshots`.
- Snapshot creation, persistence, update, replacement, deletion, and retention cleanup are classified as application-state writes and remain outside SPF-008.
- Snapshot normalization accepts canonical JSON-compatible data only.
- Normalization is deterministic and returns an immutable read model.
- Snapshot query authorization occurs before repository access.
- Authorization denial or authorization failure prevents repository execution.
- Repository and policy failures are sanitized before exposure.
- Snapshot queries do not refresh vendor data.
- Schema validation and schema drift governance remain owned by SPF-009.
- No new database or filesystem persistence is introduced.
- Production live vendor registration remains disabled.
- Ubuntu remains a stateless infrastructure worker.

Implementation commit: `d8859a3706a087f88be513e32097b22c9a8ec3d6`.

Validation baseline: 35 targeted tests passed and 872 full regression tests passed.

Next architecture task: SPF-009 Validation and Schema Drift.
<!-- SPF-008-CLOSE:END -->

<!-- AICONTROLCENTER:SPF-009:CLOSED -->
## SPF-009 Validation and Schema Drift Closure

- Status: CLOSED on 2026-07-23.
- AIControlCenter remains the single control plane and owns schema governance, authorization, validation, drift policy, monitoring, and audit boundaries.
- Canonical contract source remains `core/shopping/contracts/schemas/v1` using JSON Schema Draft 2020-12.
- Runtime validation statuses are `VALID`, `INVALID`, and `ERROR`; only `VALID` is accepted and all operational uncertainty fails closed.
- Schema resolution is local-only. Remote HTTP schema resolution and automatic fetch are forbidden.
- Drift statuses are `NO_DRIFT`, `COMPATIBLE_DRIFT`, `BREAKING_DRIFT`, and `UNKNOWN_DRIFT` from the canonical-consumer-safety perspective.
- `UNKNOWN_DRIFT` is fail-closed and no drift result automatically changes the canonical contract.
- Schema discovery remains read-only and authorization occurs before `SchemaDiscoveryPort.discover_schema(*, context, adapter_name)`.
- Schema ID and adapter name are separate concerns; no vendor DTO owns the canonical contract.
- Automatic schema adoption, migration, application-state persistence, vendor writes, production registration, and Ubuntu application state remain disabled.

<!-- AICONTROLCENTER:SPF-010:CLOSED -->
## SPF-010 Closure — Shopping Platform Foundation

- Status: CLOSED
- Shopping Platform Foundation: 10/10 (100%)
- Production Readiness Gate: PASSED for the read-only Foundation.
- AIControlCenter remains the single Control Plane on Mac mini M4.
- Ubuntu Server remains a stateless infrastructure worker only.
- AI workloads, business logic, and application state remain outside Ubuntu.
- Production write operations remain disabled.
- Automatic schema adoption and automatic schema migration remain disabled.
- Any future mutation or write capability requires a separate sprint and explicit production gate.
- Shopping regression: 233 passed.
- Full regression: 930 or more passed, 5 deselected, 0 failed, 0 errors.
- Read-only operational smoke validation: PASSED.
- Release blockers at final audit: 0.
- Architecture state: Foundation boundaries are frozen for production-readiness closure.
- External commerce and CMS components remain replaceable behind adapters and APIs.

<!-- BEGIN AICONTROLCENTER:SRI-03 -->
## SRI-03 External Read Production Architecture

AIControlCenter on the Mac mini M4 remains the single Control Plane.
Ubuntu remains a stateless infrastructure worker and owns no Shopping business logic, application state, AI workload, or ingress policy.

### Headless Shopping boundary

- WordPress is the CMS.
- WooCommerce is a replaceable Commerce Engine.
- AIControlCenter owns policy, orchestration, normalization, validation, audit, authorization, workflow, and Shopping business logic.
- External components integrate through adapters and JSON or REST contracts.

### Caddy production ingress

- Caddy runs on the Mac Control Plane.
- WAN TCP 80 forwards to Mac TCP 58080.
- WAN TCP 443 forwards to Mac TCP 58443.
- Caddy owns transport ingress only and contains no Shopping business logic.

### Production TLS identity

`bokstory.iptime.org` is an operational DDNS locator only.
It is not the production canonical TLS identity.

Authoritative DNS evidence classified the hostname as `PARENT_CAA_PROHIBITS_PUBLIC_CA_ISSUANCE`.
Production HTTPS therefore requires a platform-controlled DNS namespace.
AAAA remains absent until IPv6 ingress is separately validated.

### Evidence

- SRI-03D3A3-D8 confirmed external LTE or 5G HTTP ingress and HTTP 200.
- SRI-03D3A3-D9 discovered the inherited CAA restriction.
- SRI-03D3A3-D10 confirmed the parent CAA restriction on authoritative ipTIME nameservers.
<!-- END AICONTROLCENTER:SRI-03 -->

<!-- SRI-06B-R1:ARCHITECTURE -->
## SRI External READ and Observability Architecture

### Ownership

- core/cms owns generic CMS models, ports and WordPress normalization.
- core/cms must not import core/shopping.
- core/shopping owns commerce schema, snapshot and drift semantics.
- core/monitoring owns generic operational observation orchestration.
- ExternalReadObserver receives domain dependencies through injection and owns no network client.

### Public edge

- Host Caddy is the sole public edge.
- /healthz is an explicit infrastructure health route.
- Remaining application traffic falls back to WordPress at 127.0.0.1:58081.

### Operational evidence

- Stage order is Health, Schema, Snapshot and Drift.
- Persisted JSON is authoritative and console summaries are human-only.
- Generic observations use sanitized generic JSON snapshots.
- Shopping snapshot normalization is reserved for Shopping domain snapshots.
- Contract drift is a failure condition and business-data drift is observed separately.

### Recovery

Recovery requires immutable snapshot, scratch restore, structural validation, semantic validation, explicit authorization, production restore and production validation.
<!-- END SRI-06B-R1 -->

<!-- AICONTROLCENTER:DPL-01:START -->
## DPL Deployment Package Bounded Context

DPL is an AIControlCenter-owned bounded context for immutable desired-state
packages and observed-state reports. It preserves the Mac mini M4 as the
always-on Brain and single Control Plane.

### Ownership and dependencies

- AIControlCenter owns DPL governance, policy, orchestration, approval,
  authorization, audit and deployment control.
- DPL read observes inventory and state.
- DPL plan validates policy, computes diff and emits a dry-run plan.
- Apply is a separate future boundary; read and plan must not import or invoke
  mutating executors.
- DPL v1 uses versioned JSON Schemas and a registry.
- A DPL package is immutable and Git-identifiable; it never grants activation
  authority.

### Platform boundary

- Mac production services use launchd.
- Host Caddy is the only public edge.
- WordPress is the CMS Engine and WooCommerce is the Commerce Engine.
- AIControlCenter owns all business logic.
- Ubuntu remains optional, stateless and on demand.
- DPL-02 activates no Ubuntu adapter and excludes
  `UbuntuWorkerClient.execute`.
- Linux systemd Control Plane artifacts are `LEGACY_UNSUPPORTED`,
  production-prohibited and excluded from DPL.

DPL-02 is limited to inventory, manifest and policy validation, diff, dry-run
planning, readiness reporting and audit. Apply, install, restart, bootstrap,
rollback execution, production writes and generic Ubuntu command execution are
prohibited. Production activation is not authorized.

Canonical details: `docs/architecture/dpl-deployment-package.md`.
<!-- AICONTROLCENTER:DPL-01:END -->

## DPL M2 Readiness Boundary

`core.deployment.m2_readiness` is a pure evidence-consumer owned by
AIControlCenter on the Mac Control Plane. It imports no API, worker, runtime
adapter, command, network or persistence implementation. Its accepted result
is sandbox-only and non-production-only; it performs no activation. Ubuntu
owns no governance or audit. DPL-04 is CLOSED with
`M2 READINESS_ACCEPTED`, `M2 ACTIVATION_NOT_STARTED`, and Production activation
`NOT_AUTHORIZED`. M2-P1 policy is available but grants no execution or
activation; M2-P2 remains the next separately controlled boundary.

## M3 Permit Replay Write Boundary

M3-A2A remains the read-only inspector. M3-A2B adds a separate Mac Control
Plane-owned existing-file SQLite writer using explicit configuration,
`mode=rw`, preconfigured WAL and serialized append-only transactions. It owns
permit reservation, terminal disposition and replay integrity; Ubuntu owns
none of this state. No operational database, migration, repair, audit write or
Production activation is composed.

## M3 Permit Replay Recovery Boundary

Recovery depends only on M3-A2A public inspection/path/state contracts, M3-A2B
public writer contracts, deployment contracts and Python SQLite. Verified
temporary outputs are atomically published only after byte, canonical manifest,
ordered-ledger and derived-state equality checks. A restored file is never
automatically selected as operational.
# M3-A4B2B1B approval boundary

AIControlCenter on the Mac Brain owns the human-approval intake and permit
issuance decision. Ubuntu cannot approve, issue, claim or execute permits. The
pure `operational_permit_approval` layer consumes M3-A4B2B1A review contracts
and delegates synthetic in-memory creation to M3-A4B1 only after all gates
pass. It has no persistence, executor, API, worker, network or dispatch
dependency. Live issuance and production activation remain unauthorized.
# M3-A4B2B2A execution boundary

AIControlCenter on the Mac mini M4 is the sole owner of operational permit
validation, atomic claim and bootstrap governance. The trusted local account
home determines the exact Application Support root. Ubuntu, workers, CMS,
commerce and n8n cannot participate. M3-A4B2B2A makes the controlled
non-production capability available in code without executing it or
authorizing production.
# M3-A4B2B2B-R1 shared application-state boundary

The Mac application-state parent is shared infrastructure. Deployment control
never assumes exclusive ownership and manages only `audit`, `security`, and
`monitoring`. Existing siblings are opaque and immutable to bootstrap.
Pre-existing safe `0755` parents carry a nonblocking restriction; newly created
managed directories require `0700`.
# Controlled operational activation boundary

Operational permit issuance and controlled Mac execution require a separate,
immutable, exact-commit activation authorization. Flags and environment
variables cannot grant this authority. Test and Mac operational adapters remain
strictly separated.
# R5 acknowledgement projection boundary

The Control Plane retains complete restriction acknowledgement evidence while
projecting only the semantic `warnings-427` Mac-operator/independent-approver
pair into the executor contract. Projection is typed, immutable,
order-independent, digest-bound, and validated before issuance and claim.

# Bootstrap evidence and recovery boundary

M3-A4B3 adds a Control-Plane-owned, read-only-first evidence validator and
recovery-work-confined restore adapter. It reuses public canonical helpers and
SQLite inspectors, never restores into the operational root, and has no issuer,
claim, live-runner, writer, monitoring, dispatch, network, Ubuntu, or business
logic capability. Snapshot permissions may be a read-only subset of the
created `0700`/`0600` state; broader permissions always fail closed.

# Controlled activation validation boundary

M3-A4C adds a pure immutable AIControlCenter closeout boundary. It validates
Git, evidence, recovery, health, control-plane, Mac-role, Ubuntu-exclusion, and
default-deny facts and emits deterministic JSON. It has no activation, issuer,
claim, restore, API, remote, worker, or business-logic capability. Success
requires a future independent architecture and authorization gate.

# M4 controlled activation architecture boundary

M4-A1 adds a closed typed capability registry, immutable per-capability state
machine, default-deny architecture policy, deterministic planner, and
validation facade. Capabilities cannot authorize or add dependencies
implicitly. AIControlCenter on Mac owns every governance, authorization, audit,
replay, and activation boundary; Ubuntu is ineligible. The package imports only
pure deployment contracts, exposes no runtime port, and cannot activate a
writer, monitor, dispatch, command, API write route, or production transition.

# M4 capability authorization contract boundary

M4-A2 adds immutable capability-scoped request, approval, restriction, evidence,
validation, and grant-plan contracts. Canonical JSON, SHA-256 binding, injected
UTC-aware time validation, independent identity policy, a maximum one-hour
window, and exact M3/M4-A1 bindings fail closed. Each M4-A1 capability is
requested alone; dependency references never imply authorization.

The grant contract is a test-only deterministic plan with authorization,
permit, claim, and activation fields false. No runtime port, API write route,
command, network client, writer, monitoring runtime, dispatch, Ubuntu
delegation, or production path exists. The decision
`READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION` authorizes nothing.

# M4 test-only authorization simulation boundary

M4-A3 is pure and in-memory with injected time and seed. Its seven simulated
states are separate from the operational state machine and never enter
`CONTROLLED_ACTIVE`. Artifacts use namespace `m4-a3-test-only` and immutable
test-only, operational-invalid, non-production, Ubuntu-excluded, and
runtime-denied markers. Each capability owns an independent digest chain and
one process-local claim; dependencies are references only. Strict shape checks
and unconditional live-boundary rejection prevent marker deletion or field
renaming from producing an operational artifact. No operational store, writer,
runtime port, command, network, API write, Ubuntu, or activation dependency
exists.
# AUTO-01 control-plane boundary

AIControlCenter exclusively owns autonomous-delivery governance, policy,
roadmap compilation, scheduling, dependency planning, approvals, authorization,
retry and recovery decisions, evidence gates, completion and deployment
control. Codex is a bounded replaceable executor port, never an authority.

AUTO-01 adds pure typed contracts, fail-closed manifest validation, canonical
SHA-256 JSON, deterministic DAG compilation and a strict delivery lifecycle. It
adds no persistent runner, subprocess, network adapter, launchd service or
operational side effect. L4/L5 and post-claim recovery require human approval;
production remains `NOT_AUTHORIZED`. AUTO-02 owns the future persistent runner
and terminal-independence design.

<!-- SHOPPING-FIRST-REPRIORITIZATION:BEGIN -->
## Shopping-First Service Architecture

AIControlCenter remains the single control plane and owns business
logic, governance, orchestration, authorization, adapters and audit
references.

Replaceable open-source components retain their specialized roles:

- WordPress: CMS
- WooCommerce: Commerce Engine
- n8n: Automation Engine
- Ollama: Local Model Runtime
- OpenClaw: Assistant Interface
- GitHub: Source, CI and release evidence

General-purpose capabilities use replaceable open-source components.
Custom implementation requires a documented capability gap.

Service progression is Shopping Platform, then AI Integration Platform,
then Personal AI Assistant. Ubuntu remains a stateless infrastructure
worker and owns no orchestration or application state.
<!-- SHOPPING-FIRST-REPRIORITIZATION:END -->

<!-- SHOP-00-CLOSEOUT:BEGIN -->
## SHOP-00 Shopping Platform Reprioritization

SHOP-00 is closed.

Repository inventory and regression validation confirmed that the
existing Shopping Platform Foundation and Shopping External Read
Integration are already part of the current branch history.

Existing capabilities designated for reuse:

- WooCommerce external read adapter
- WooCommerce transport and normalization
- WordPress CMS adapter
- normalized product snapshot JSON contracts
- read authorization and deny-by-default policy
- schema validation and drift monitoring
- adapter health monitoring
- nine read-only Shopping API routes
- Orange Coco storefront

The former SHOP-01 WooCommerce Read Adapter scope is therefore
`CLOSED_BY_EXISTING_SRI`.

The first incomplete product capability is:

`SHOP-01_PRODUCT_MANAGEMENT_READ_MODEL_AND_DASHBOARD`

Architecture invariants:

- Storefront and management Dashboard are separate surfaces.
- Dashboard consumes AIControlCenter APIs only.
- Dashboard does not call WooCommerce directly.
- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns business workflow and normalized management
  views.
- SHOP-01 is read-only.
- Product draft, approval and controlled write remain separate tasks.
- No Shopping business logic is placed on Ubuntu.
- Production writes remain `NOT_AUTHORIZED`.
<!-- SHOP-00-CLOSEOUT:END -->

<!-- SHOP-01B-MANAGEMENT-READ-MODEL:BEGIN -->
## SHOP-01B Shopping Management Read Model

SHOP-01B adds a pure read-only application projection for
operator-facing product management data.

The projection consumes the existing `ShoppingService` boundary and
produces deterministic JSON-safe output containing:

- service health
- readiness
- read/write capability state
- adapter integration state
- catalog totals
- in-stock and out-of-stock counts
- inventory quantity totals
- normalized product list fields

The module performs no network calls, persistence, product mutation,
WooCommerce imports or Dashboard registration.

The Product Management Dashboard remains a projection of WooCommerce
truth through AIControlCenter. It is not a second product database.

The next task is `SHOP-01C_DASHBOARD_JSON_INTEGRATION`.
<!-- SHOP-01B-MANAGEMENT-READ-MODEL:END -->

<!-- SHOP-01C-DASHBOARD-INTEGRATION:BEGIN -->
## SHOP-01C Dashboard JSON Integration

The existing `GET /dashboard` projection now includes an optional
`shopping_management` section.

The section is generated through the completed Shopping management
read model and remains read-only.

Failure isolation rules:

- Shopping configuration failure does not fail the Dashboard.
- Shopping catalog failure does not fail the Dashboard.
- Internal exception details are never exposed.
- An unavailable Shopping dependency returns a deterministic
  `UNAVAILABLE` envelope.
- Existing Dashboard behavior is preserved when no Shopping
  projection is injected.

The Dashboard imports no WooCommerce adapter and creates no local
product truth.

The next task is `SHOP-01D_VALIDATION_AND_CLOSEOUT`.
<!-- SHOP-01C-DASHBOARD-INTEGRATION:END -->

<!-- SHOP-01D-CLOSEOUT:BEGIN -->
## SHOP-01 Product Management Read Model and Dashboard

SHOP-01 is closed.

Completed capabilities:

- deterministic Shopping management read model
- product and inventory summary
- normalized operator-facing product list
- health, readiness, capability and integration projection
- optional `shopping_management` Dashboard dependency
- `GET /dashboard.shopping_management` JSON projection
- deterministic `UNAVAILABLE` failure envelope
- internal error-detail suppression
- source and result mutation isolation
- existing Dashboard compatibility
- default-configuration read-only operational observation

Architecture boundaries remain unchanged:

- WooCommerce remains the Commerce Engine.
- WordPress remains the CMS.
- AIControlCenter owns management projections and workflow logic.
- The Dashboard does not import WooCommerce adapters.
- No local product truth was created.
- No Shopping mutation route was added.
- Production writes remain `NOT_AUTHORIZED`.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01D-CLOSEOUT:END -->

<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:BEGIN -->
## SHOP-01E2 Shopping Product Compatibility Adapter

The default Mock catalog returned the legacy `Product` contract while
the management read model required the canonical product projection.

A dedicated application adapter now translates the existing
`ShoppingService` result into the canonical management contract.

Explicit mappings:

- `id` to `product_id`
- `image_url` to `image_urls`
- `Decimal` price to a JSON number

Missing SKU, inventory quantity, URL and updated timestamp values
remain null. The adapter does not synthesize unknown Commerce data.

The canonical management contract was not weakened. The Dashboard
continues to have no direct WooCommerce dependency.

The next task is:

`SHOP-01E3_WOOCOMMERCE_READ_ONLY_CONFIGURATION`
<!-- SHOP-01E2-COMPATIBILITY-ADAPTER:END -->

<!-- SHOP-01E3C-SECURE-RUNTIME:BEGIN -->
## SHOP-01E3C Secure WooCommerce Read Runtime

AIControlCenter now provides a reusable secure runtime loader for the
existing WooCommerce read-only credential file.

The loader validates:

- a regular non-symlink credential file
- current-user ownership
- file mode `0600`
- direct parent mode `0700`
- exact credential keys
- read-only WooCommerce API permission

Credential values are not copied into Git, LaunchAgent plist files or
the process environment.

Runtime selection uses the non-secret profile:

`AICONTROLCENTER_SHOPPING_PROFILE=woocommerce_read_only`

The profile is not enabled persistently by this task. Persistent
LaunchAgent activation requires a separate operational authorization.

The canonical WooCommerce target currently has zero products and one
product category. This is a valid empty Commerce Engine state, not an
adapter failure.

The next active task is:

`SHOP-02A_PRODUCT_DRAFT_WORKFLOW_ARCHITECTURE`
<!-- SHOP-01E3C-SECURE-RUNTIME:END -->

## SHOP-02A Product Draft Boundary

AIControlCenter owns immutable ProductDraft revisions, validation, human review, authorization/audit references and non-executable deployment intent. WooCommerce remains commerce product truth; WordPress remains the CMS Engine; Ubuntu owns no workflow state. Approval is human-only and exact-revision-bound. `DEPLOYMENT_READY` is not deployment, and production writes remain `NOT_AUTHORIZED`. See `docs/architecture/SHOP-02A-PRODUCT-DRAFT-WORKFLOW.md`.

## SHOP-02B Product Draft Domain

The ProductDraft 1.0.0 domain is implemented under `core/shopping/product_drafts/` as immutable values and revisions with a pure, closed lifecycle evaluator. Exact revision concurrency and SHA-256 canonical-JSON idempotency are mediated through a replaceable repository port. Its only adapter is isolated in memory and is explicitly non-production. There is no mutation API, durable store, WooCommerce write, or production activation. SHOP-02C adds validation and human-approval application services next; production writes remain `NOT_AUTHORIZED`.

## SHOP-02C Product Draft Application Boundary

Application services under `core/shopping/product_drafts/application/` validate canonical immutable revisions and orchestrate REQUEST_REVIEW, APPROVE, REJECT, and REVOKE through the existing lifecycle evaluator. Authorization is replaceable and deny-by-default; accepted decisions require exact resource binding and HUMAN reviewers for decision operations. Deterministic audit references and command idempotency are instance-local and in-memory only. ProductDraft contracts remain 1.0.0. There are no mutation routes, Commerce writes, persistent stores, or production activation; production writes remain `NOT_AUTHORIZED`. SHOP-02D adds the read API and Dashboard projection next.
# SHOP-02D read boundary

ProductDraft query ownership remains in AIControlCenter. A replaceable `ProductDraftReadSource` supplies immutable snapshots to deterministic JSON-safe queries and the `product_draft_review` Dashboard projection. The default runtime source is safely unavailable, while an empty configured source is available with zero results. WooCommerce remains published product truth; this boundary has no writes or persistence and ProductDraft contracts remain 1.0.0.

## SHOP-03A controlled Commerce write architecture

Approved immutable ProductDraft revisions can now be evaluated into an immutable controlled write plan through explicit freshness, exact source/revision/intent binding, deny-by-default authorization, and instance-local idempotency. Only a deterministic fake/dry-run adapter exists. No API mutation route, persistent queue, network dependency, or real Commerce mutation exists. ProductDraft contracts remain 1.0.0; production writes are `NOT_AUTHORIZED`, and SHOP-03B is separately gated. See `docs/architecture/SHOP-03A-CONTROLLED-WOOCOMMERCE-WRITE.md`.
# SHOP-03B1 Commerce write adapter boundary

The ProductDraft deployment package owns the controlled WooCommerce write port without coupling to the existing read adapter. An immutable SHOP-03A plan carries its digest-bound proposed fields into an explicit WooCommerce allowlist. Credentials arrive from an injected call-time provider and never enter request metadata. A synchronous injected transport receives the safe request, credential value, and bounded timeout as separate arguments. No concrete transport exists; defaults fail closed.

Responses are reduced to allowlisted fields and deterministic digests, then reconciled as `MATCHED`, `MISMATCH`, `REMOTE_IDENTIFIER_MISMATCH`, `RESPONSE_INVALID`, `TRANSPORT_UNAVAILABLE`, or `CREDENTIAL_UNAVAILABLE`. No retry or compensating write exists. SHOP-03B1 is intercepted validation only and cannot claim `LIVE_APPLIED`.
## UI-01 presentation boundary

`GET /homepage` is a package-local HTML/CSS/JavaScript operator view on the
existing Homepage router. Presentation reads only `GET /dashboard`; Shopping,
ProductDraft, approval, deployment, and Commerce-write authority remain in
their existing owners. ProductDraft and deployment contracts are unchanged.
Public exposure remains pending OPS-01 and production writes remain
`NOT_AUTHORIZED`.

## UI-02 Product Management presentation boundary

`GET /homepage/product-management` is package-local presentation on the existing
Homepage router. It consumes only the three existing same-origin ProductDraft
GET resources. AIControlCenter retains lifecycle, validation, review,
deployment-intent, policy, and audit authority; WooCommerce retains public
Commerce truth and the browser has no business or write authority. There is no
public exposure or production activation. Next:
`OPS-01_STAGING_CADDY_AUTH_MONITORING`.

## Runtime Source Isolation Requirement

A production Runtime identity must identify both its Python dependency
environment and its application source.

The mutable AIControlCenter Git working tree must not be treated as the
production application-source artifact.

Target runtime layout:

`runtime/venvs/<runtime-id>`

and:

`runtime/sources/<runtime-id>`

must represent the same approved release identity.

The production wrapper must resolve application source from the immutable
runtime source artifact and must fail closed when source identity, runtime
identity, or expected commit do not match.

## PI-009A2 Runtime Source Isolation

PI-009A2 freezes a paired immutable Runtime artifact model:

- `runtime/venvs/<runtime-id>` — Python dependency environment
- `runtime/sources/<runtime-id>` — immutable tracked application source

`runtime/current` continues to select the venv Runtime identity.

The production wrapper must derive the matching source artifact from the same
Runtime ID and must require exact full source-commit agreement.

The mutable Git working tree is not a valid production application source.

## Immutable Live Runtime Boundary

The live AIControlCenter shadow service uses:

- Runtime: `runtime/venvs/7b171f135dc7`
- Source: `runtime/sources/7b171f135dc7`
- State: `~/Library/Application Support/AIControlCenter/data`

Mutable Git source and repository-local SQLite state are outside the live
application boundary.

## Production Authorization Boundary

PI-009 Production authorization is represented as governance evidence tied to
an exact immutable Runtime/source identity.

Production authorization does not mutate the immutable source artifact.

Current authorized deployment:

- Runtime: `7b171f135dc7`
- Source commit: `7b171f135dc7882546bf7f733208778f1aef4943`
- Runtime source: immutable
- Persistent state: external macOS application data root
- Control Plane: AIControlCenter on Mac mini M4
- Ubuntu role: stateless infrastructure worker

## AI Provider Candidate Deployment Boundary

AI-PROVIDER-01C-B produced the non-active deployment pair:

- Candidate Runtime: `runtime/venvs/102b8f1fa862`
- Candidate source: `runtime/sources/102b8f1fa862`
- Source commit: `102b8f1fa8628d00d25575cb94538826a1a04e10`

Candidate validation runs from the immutable source with matching Runtime
Python and external temporary state. FakeProvider is the network-free workflow
boundary. Candidate existence is not activation authority: Production remains
on `7b171f135dc7`, and AI-PROVIDER-01C-C requires separate explicit promotion
authorization.

## Production AI Provider

Active Runtime:

`102b8f1fa862`

Canonical Control Plane path:

`BrainAgent -> ProviderRouter -> ProviderAdapter -> OpenAIAdapter`

AIControlCenter owns provider selection, governance and business logic.

Vendor-specific transport remains isolated behind ProviderAdapter.

Automatic cross-provider fallback remains prohibited.

Persistent daemon credential delivery is owned by SEC-01.

# SEC-01C-R1 immutable-source repair

SEC-01C consumed two installs and one restart. Its frozen wrapper preserved secret injection but used mutable repository cwd and `PYTHONPATH`; HTTP recovery did not satisfy the immutable Production gate, and no automatic rollback occurred. The repository wrapper now dynamically pairs `runtime/venvs/<ID>` and `runtime/sources/<ID>` from `runtime/current`, verifies identity/content, preserves external data, isolates `PYTHONPATH`, enters immutable source, and uses Runtime Python `-P`. It is not installed by R1; the current live installation remains blocked pending new exact human authorization for replacement and one restart. Runtime `102b8f1fa862` has importable `jsonschema`; Notion remains `DEFERRED_UNTIL_FINAL_PHASE`.
# Security architecture update (SEC-01B)

Provider credentials follow [Protected File-Per-Provider Secrets with Deterministic Wrapper Injection](docs/architecture/PROVIDER-SECRET-DELIVERY.md): external protected storage, wrapper-owned validation/injection, and environment-backed adapter consumption. Business logic has no secret-file responsibility.

## SEC-01C Production secret delivery closeout

SEC-01C is `COMPLETE`; milestone `PRODUCTION_DAEMON_SECRET_DELIVERY_VALIDATED`.
After R1 restored immutable-source execution, R2 identified the workers config as
`VERSIONED_APPLICATION_CONFIG`, R3 froze its immutable-source binding without an
intended live mutation, R3Q stopped on precondition drift with zero edits and
restarts, and separately authorized R3Q2 performed one representation-only
worker.env correction plus exactly one restart. The daemon now has no mutable
repository source/config dependency, and provider-secret presence was validated
without value exposure or provider network calls. SEC-01 remains open; next is
SEC-01D Secret Lifecycle & Recovery Validation. Notion is
`DEFERRED_UNTIL_FINAL_PHASE`. See
[the closeout](docs/operations/SEC-01C-PRODUCTION-SECRET-DELIVERY-CLOSEOUT.md).

## SEC-01 Production provider-secret lifecycle architecture

SEC-01 is complete at `PRODUCTION_SECRET_LIFECYCLE_VALIDATED`. The Mac mini M4
is the always-on Brain and AIControlCenter is the single Control Plane. Ubuntu
remains an optional stateless infrastructure Worker consumed through JSON APIs;
it owns no AI workload, business logic, application state, governance,
authorization, or provider-secret policy. Operations remain headless and
Git-first.

Provider credentials use **Protected File-Per-Provider Secrets with
Deterministic Wrapper Injection**. The deterministic service wrapper validates
and injects protected provider files; business logic never reads secret files.
There is no `launchctl setenv` persistence, plaintext secret in a plist, or
silent cross-provider fallback. Missing or invalid provider material fails
closed, and no credential value or identifier belongs in documentation.

Production is immutably bound to Runtime `102b8f1fa862` and source
`/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/sources/102b8f1fa862`.
A desired state or staged candidate is not activation authority. Every
Production mutation requires explicit, scope-bounded human authorization; a
failed controlled mutation authorizes neither automatic rollback nor retry.

Authoritative reboot-crossing evidence belongs under
`/Users/kyouhan/Library/Application Support/AIControlCenter/governance/evidence/SEC-01`;
`/private/tmp` is not authoritative across reboot. Permanent exceptions are:

- `SEC-01D-B-REPEATED-RESTART-AUTHORIZATION-SCOPE-EXCEPTION`: D-B ran the
  restart workflow twice under authorization for exactly one. This was not
  retroactively authorized or erased, although Production remained healthy.
- `SEC-01D-C3-BOOT-PARSER-DEFECT`: greedy parsing captured `usec` instead of
  `sec`; the original reboot authorization became `STALE_UNCONSUMED`, and C3-R1
  corrected the parser before the authorized reboot.
- `SEC-01D-C5-EVIDENCE-RETENTION-DEFECT`: reboot evidence in `/private/tmp` was
  lost. C5-R2 used transcript-bound recovery. Exact reboot count was no longer
  machine-verifiable; the operator attested one reboot and boot epoch proved a
  reboot boundary. Lost C3/C4 files were not restored.

The final regression gate uses the canonical deployment harness
`ops/macos/validation/run-deployment-regression-gate.sh`. It provisions
`AICONTROLCENTER_GIT_EVIDENCE_TEST_ROOT`,
`AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_ROOT`, and
`AICONTROLCENTER_OPERATIONAL_LIVE_TEST_ROOT`, then forwards selectors with
`python -m pytest "$@"`. FINAL R1 bypassed that contract with raw pytest and
reported 2 failed, 2338 passed, 5 deselected, and 62 errors; it is retained as
`INVALID_RAW_PYTEST_GATE_INVOCATION`, not an application or documentation
failure. FINAL R2 diagnosed this read-only with no mutation. FINAL R3 passed
3/3 representative selections (17 tests) through the harness. Authoritative
FINAL R4 used the canonical harness and passed 2402 tests with 5 deselected and
437 warnings; warnings are not failures. Tests did not modify the repository,
Production PID was unchanged, canonical secret metadata was preserved, the
candidate was absent, and Production mutation was zero.

<!-- AIHD_RUNTIME_HEALTH_PRODUCTION_2026_08_13 -->
## OPS-01B Application Scheduler log readiness

Application Scheduler lifecycle readiness includes an explicit launchd log
contract. `/var/log/aicontrolcenter` must remain a real `root:wheel 0755`
directory. The Scheduler stdout and stderr paths must each be real,
non-symlink `kyouhan:staff 0640` files.

The existing `core.runtime.service_health.ServiceHealth` runtime-observation
projection receives this contract through its application composition adapter
and fails overall health closed when required Scheduler log readiness is
missing, invalid, or cannot be inspected. It imports no `ops.*` adapter.
The immutable Production runner launches `ops.macos.runtime.application:app`.
That outer macOS composition root injects
`application_scheduler_logs.inspect_contract` into the platform-neutral
`core.api.app.create_app(...)` factory; the core default remains fail-closed.
`application_scheduler_bootstrap.py` is the canonical Scheduler deployment
lifecycle gate. It consumes the same read-only log contract and performs the
service-registration eligibility probe in dry-run and apply modes. Apply alone
may issue exactly one bootstrap after all gates pass.
`application_scheduler_logs.py validate` exposes the same read-only contract.
Its separate bounded `provision` primitive may create only missing files;
it does not remediate an invalid existing object, invoke `launchctl`, retry,
roll back, bootstrap, or kickstart. Root identity is only a local execution
precondition, not human authorization. The outer governed executor owns and
must consume authorization immediately before each bounded Production
invocation.

Application Scheduler Production recovery was already operational before this
recurrence-prevention closeout. Focused recurrence validation passed. The first
canonical deployment regression invocation then failed with 13 test failures:
Scheduler fixtures were sensitive to the process umask, and one controlled-live
test hashed the independently mutable real-home AIControlCenter tree. Those
defects were corrected only in tests, without weakening Product contracts. The
corrected focused scope passed 39 tests under umask `077`, with the controlled
live root explicitly confined to `/private/tmp`. Because test changes followed
the first invocation, the canonical regression was invoked exactly twice; the
second invocation passed with `RC=0`. No canonical test count is asserted for
that passing invocation.

No Production mutation occurred during recurrence-prevention validation. No
additional activation, bootstrap, log provisioning, kickstart, retry, or
rollback was performed. OPS-01B recurrence prevention is validated, and
OPS-01B is closed. WordPress and Shadow work remain separate future work.

## Production Runtime Health Operational Contract — 2026-08-13

The Runtime Health model is deployed to Production release
`ed2424e39bb1`
(`ed2424e39bb12e363ae7a1967c677e661ae7ec0e`).

The Mac mini remains the AIControlCenter Control Plane.
The Production API lifecycle is owned by launchd service
`com.aicontrolcenter.api` and serves the canonical API on
`127.0.0.1:58081`.

The production service-topology projection is:

- `aicontrolcenter-api`: required, launchd-managed, `RUNNING`.
- `telegram`: optional and currently `NOT_DEPLOYED`.
- `application-scheduler`: required and currently `NOT_DEPLOYED`.
- Scheduler heartbeat: currently `STALE`.
- Topology contract: `VALID`.
- Aggregate Runtime Health: `healthy=false` until the required Application
  Scheduler is deployed and its heartbeat becomes fresh.

`healthy=false` in this state is an intentional truthful degraded-state
projection, not an API deployment failure.

The Homepage scheduler projection and the Runtime Health
`application-scheduler` lifecycle projection are different operational
concepts. An application-level scheduler status such as `ONLINE` must not be
interpreted as proof that the dedicated launchd Application Scheduler service
is deployed.

### Production ingress contract

Public ingress is:

`WAN :80/:443`
→ router forwarding
→ Mac Caddy `:58080/:58443`
→ canonical API `127.0.0.1:58081`.

Shadow `127.0.0.1:18100` is not a public Caddy upstream.

### Candidate-validation contract

A candidate release must be capable of Shadow validation without changing the
Production `runtime/current` pointer.

Release `ed2424e39bb1` was validated using a pinned ephemeral candidate lane on
`127.0.0.1:18101`, while the canonical API, existing Shadow and public ingress
remained unchanged.

Known deployment-tooling debt is tracked separately:

- the existing Shadow runner derives its effective Runtime/Source selection
  from `runtime/current` before its runtime-link override is processed;
- the legacy Shadow executor contains automatic external rollback behavior that
  does not match the current one-authorization/one-bounded-mutation governance
  model.

## PA-05 — WooCommerce Headless Adapter v1

PA-05 is validated at milestone
`WOOCOMMERCE_HEADLESS_ADAPTER_V1_VALIDATED`. AIControlCenter remains the sole
Control Plane and owner of shopping business logic. `core.shopping` is
authoritative for ProductDraft lifecycle, product policy, workflow,
recommendation, customer automation, governance, and business logic.
WordPress is CMS-only; WooCommerce is commerce-engine-only;
`integrations.woocommerce` is replaceable and read-only. The outer composition
root is `ops.macos.runtime.application`; core imports neither `ops.*` nor
`integrations.*` (`CORE_OPS_IMPORT_COUNT=0`,
`CORE_INTEGRATIONS_IMPORT_COUNT=0`).

The canonical Production manifest contains no WooCommerce service identity.
Absence is not interpreted as `NOT_DEPLOYED`: deployment, configuration, and
authentication remain `UNKNOWN`, catalog/API availability is unproven, and
the default capability status is fail-closed `UNAVAILABLE`. Lookup failures
that are missing, duplicate, malformed, schema-invalid, or unreadable invent
no `canonical_manifest` evidence. Validated manifest evidence is emitted only
when exactly one WooCommerce identity is returned successfully.

`core.capabilities` owns governance. Its reserved facts cannot be overridden
by integrations: `authority=AICONTROLCENTER`, `read_only=true`,
`production_authorization=false`, `infrastructure_mutation=false`,
`platform_business_policy_ownership=false`, and `action_execution=false`.
`CapabilityGovernanceExtensions` is typed and boolean-only; WooCommerce adds
only `commerce_engine_only=true` and `automatic_retry=false`.

The provider-neutral `UnavailableCapabilityObserver` consolidates unavailable
fallbacks. Platform-neutral `create_app` performs no WooCommerce, n8n, or
OpenClaw external discovery, preserving PA-02 and PA-03 outward fail-closed
compatibility. PA-05 exposes only `GET /shopping/providers/woocommerce`; it
adds no mutation endpoint or product, order, inventory, customer, coupon,
execute, retry, or Production mutation action.

Final focused validation passed 91 tests after the final architecture
correction. Canonical deployment regression passed `RC=0` and was executed
exactly once for PA-05. No Production WooCommerce request, WordPress or
WooCommerce mutation, Shopping SQLite mutation, external commerce I/O, or
Docker, launchd, `runtime/current`, Caddy, Ubuntu, credential, database,
plugin, or theme mutation occurred.

Next production sprint: `SHOP-CMS-01 — WordPress + WooCommerce Runtime
Foundation`. It will establish runtime, persistent-state, secret, backup,
health/readiness, manifest, and activation architecture before public
storefront exposure. This does not claim an existing Production
WordPress/WooCommerce runtime, public storefront availability, or Notion
synchronization.

## SHOP-CMS-01A — Runtime Foundation Phase A

SHOP-CMS-01A is validated and closed at milestone
`SHOPPING_RUNTIME_FOUNDATION_VALIDATED`. The Mac mini M4 owns the single
`shopping-runtime` lifecycle (`docker-compose-on-colima`, `NOT_DEPLOYED`);
WordPress and MariaDB are components, while WooCommerce is the hosted
`wordpress-plugin-commerce-engine` capability with
`activation_authorized=false`. AIControlCenter remains the sole Control Plane
and retains shopping business logic, governance, authorization, audit,
orchestration, and deployment control. Ubuntu remains stateless and owns no
shopping application or commerce state.

Phase A validated fail-closed read-only inspection, Mac-owned named volumes
`ai-shopping-wordpress` and `ai-shopping-database`, logical database export,
WordPress archive/checksum/metadata verification, loopback-only WordPress, no
MariaDB host port, separated untracked credentials, and bounded mutation
governance. Canonical #1 found only two stale service-count expectations
(`3151 passed, 2 failed, 5 deselected`); corrections passed targeted (2),
focused compatibility (47), and canonical #2 (`RC=0`). Exactly two canonical
invocations were used. Core direct outer-package import counts remain zero.

No Production, Docker, Colima, WordPress, WooCommerce, commerce database,
Caddy, or Ubuntu mutation occurred. No runtime, WordPress, MariaDB,
WooCommerce, storefront, Caddy storefront route, or Notion sync is claimed.
Next: `SHOP-CMS-01B — bounded Production runtime activation`, milestone
`SHOPPING_RUNTIME_ACTIVATED`; future storefront milestone
`SHOPPING_STOREFRONT_ONLINE_READ_ONLY`.

## SHOP-CMS-01B — Runtime Foundation activation phase correction

The desired shopping WordPress host port is `58082`, published only as
`127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80`; MariaDB remains unpublished. The
runtime inspector derives reserved Control Plane ports from the canonical
service manifest. A healthy runtime that publishes WordPress on a reserved
Control Plane port fails readiness with `error_type=PortCollision`. The
ingress contract fixture derives the same `SHOPPING_WORDPRESS_PORT=58082`.

Compose inspection remains read-only and fail-closed. Its bounded parser
accepts a JSON array, one JSON object, NDJSON, or empty output; malformed,
scalar, or non-object content is rejected. A valid empty observation is
distinct from malformed inspection. Container health never proves
WooCommerce readiness; plugin/API and catalog readability require separate
read-only evidence.

One dedicated Colima-start authorization was consumed exactly once, and the
start succeeded. Subsequent reconciliation was read-only, not a new
Production mutation. Existing stored WordPress and MariaDB containers became
running/healthy under restart policy, with persistent volumes observed; this
was a side effect of the authorized Colima start, not an independently
authorized Compose up. The live WordPress publisher was observed on reserved
FastAPI port `58081` and is therefore `PortCollision`; the earlier REST 404
was FastAPI's response, not WordPress evidence. No cutover to `58082` has
occurred, shopping bootstrap secret files were absent, and WooCommerce
readiness remains unproven.

Canonical service and capability status remains `NOT_DEPLOYED`, and
`SHOPPING_RUNTIME_ACTIVATED=false`. Desired state is not activation authority:
the next operation is a separate human-authorized port cutover to `58082`,
followed by read-only reconciliation. WooCommerce bootstrap/readiness and
`SHOP-STOREFRONT-01` remain later work. AIControlCenter remains the sole
Control Plane; Host Caddy the sole public edge; Ubuntu remains stateless.
## CURRENT AUTHORITATIVE — Macro-WU07 Closeout

- `MACRO_WU_06=CLOSED`; WU06 was not reopened (`WU06_REOPEN_REQUIRED=false`).
- `MACRO_WU_07=CLOSED`
- `MACRO_WU_07_DISCOVERY_GATE=PASS`
- `EXISTING_DECISION_PRIMITIVE_FOUND=true`
- `NEW_CODE_REQUIRED=false`
- `ARCHITECTURE_FREEZE_REQUIRED=false`
- `RECOVER_DECISION_INPUT=EVIDENCE_INCOMPLETE`
- `RECOVER_EVIDENCE_SUFFICIENT=false`
- `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`
- `REMAINING_AUTHORITATIVE_MACRO_WUS=5`
- `AUTHORITATIVE_REMAINING_RANGE=WU08-WU12`
- `NEXT_STEP=MACRO_WU_08_CONCRETE_VALIDATOR_PREPARATION`
- `PRODUCTION_ACCESS_REQUIRED=false`; no Production access occurred during WU07.
- `FILESYSTEM_ACCESS_REQUIRED=false`; no filesystem access occurred during WU07.
- `MARIADB_ACTIVITY=NONE`
- `SQL_EXECUTION=NOT_PERFORMED`
- `PYMYSQL_ACTIVITY=NONE`
- `SECRET_VALUES_READ=NO`
- `MAC_CONTROL_PLANE=true`; Mac AIControlCenter remains the sole Control Plane.
- `UBUNTU_AUTHORITY=false`; Ubuntu retains zero Control Plane authority.
- `GOVERNANCE_CORE_CHANGED=false`
- `SEC_02_CHANGED=false`
- `CONTROLLED_EXECUTION_PORT_COUPLED=false`
- `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`
- `CANONICAL=NOT_RUN`
- `BLOCKER=NONE`

## Prior authoritative record — Macro-WU08 Closeout

- `MACRO_WU_06=CLOSED`; WU06 was not reopened.
- `MACRO_WU_07=CLOSED`; WU07 was not reopened.
- `MACRO_WU_08=CLOSED`
- `WU08_IMPLEMENTATION_GATE=PASS`
- `WU08_CORRECTION_GATE=PASS`
- `TEST_GIT_STATE_COUPLING_GATE=PASS`
- `SQL_SINGLE_STATEMENT_GATE=PASS`
- `FOCUSED_TEST_GATE=PASS`; `FOCUSED_RESULT=32 passed`.
- `FINAL_CODE_REVIEW_GATE=PASS`
- `CANONICAL_REGRESSION_GATE=PASS`; `CANONICAL_RESULT=4076 passed, 5 deselected, 555 warnings`.
- `IMPLEMENTATION_COMMIT=303e4ea`
- `WU08_IMPLEMENTATION_GIT_CLOSEOUT=COMPLETE`
- `CONCRETE_MARIADB_CONTINUITY_VALIDATOR_REPOSITORY_IMPLEMENTED=true`
- `CONCRETE_MARIADB_CONTINUITY_VALIDATOR_REPOSITORY_VALIDATED=true`
- `PRODUCTION_VALIDATION_AVAILABLE=false`
- `PRODUCTION_ACCESS_PERFORMED=false`
- `PROTECTED_SOURCE_ACCESS_PERFORMED=false`
- `CREDENTIAL_VALIDATION_PERFORMED=false`
- `MARIADB_CONNECTION_PERFORMED=false`
- `SQL_EXECUTION_PERFORMED=false`
- `PRODUCTION_AUTHORIZATION_CONSUMED=false`
- `RECOVER_DECISION_INPUT=EVIDENCE_INCOMPLETE`
- `RECOVER_EVIDENCE_SUFFICIENT=false`
- `RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT`
- `GOVERNANCE_CORE_CHANGED=false`
- `SEC_02_CHANGED=false`
- `CONTROLLED_EXECUTION_PORT_COUPLED=false`
- `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`
- `MAC_CONTROL_PLANE=true`; Mac AIControlCenter remains the sole Control Plane.
- `UBUNTU_AUTHORITY=false`; Ubuntu remains a stateless infrastructure worker with zero Control Plane authority.
- `REMAINING_AUTHORITATIVE_MACRO_WUS=4`
- `AUTHORITATIVE_REMAINING_RANGE=WU09-WU12`
- `NEXT_STEP=MACRO_WU_09_MARIADB_LOOPBACK_PORT_DEPLOYMENT`

WU08 does not authorize WU09, WU10, or WU11 and creates no reusable Production authority.
