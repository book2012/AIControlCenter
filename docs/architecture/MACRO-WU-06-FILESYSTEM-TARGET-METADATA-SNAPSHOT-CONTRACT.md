# MACRO-WU-06 Filesystem Target Metadata Snapshot Architecture Contract

## 1. Status and scope

`FILESYSTEM_METADATA_SNAPSHOT_DISCOVERY_GATE=PASS`, `BLOCKER=NONE`, and this
architecture is frozen. This is architecture documentation only. It does not
implement or execute the request, snapshot, or adapter; observe a filesystem;
access protected evidence; acquire content; or access Production.

The proposed implementation scope is exactly:

```text
core/secrets/mariadb_continuity_filesystem_target_metadata_snapshot.py
ops/macos/shopping/mariadb_continuity_filesystem_target_metadata_snapshot_adapter.py
```

The proposed inert test scope is exactly:

```text
tests/test_sm_mariadb_continuity_filesystem_target_metadata_snapshot.py
tests/test_sm_mariadb_continuity_filesystem_target_metadata_snapshot_adapter.py
```

Those files are future implementation work and are not created or modified by
this freeze.

## 2. Request value and repository construction

`FilesystemTargetMetadataSnapshotRequest` is immutable, slotted, uses
`init=False`, prohibits direct public construction, and is constructed only by
a repository factory. Its exact fields are:

```text
concrete_path: ConcreteProtectedEvidencePath
ownership_expectation: TrustedOwnershipExpectation
```

The factory consumes exactly those existing repository values. The request is
factual and grants zero authority. It has no additional factual or authority
field and accepts no raw caller path, UID, GID, mode, group, policy, retry,
fallback, authorization, capability, Production authority, or filesystem
authority.

## 3. Fail-closed pre-I/O validation

Before any filesystem observation, the future boundary validates without
coercion:

```text
type(request) is FilesystemTargetMetadataSnapshotRequest
type(request.concrete_path) is ConcreteProtectedEvidencePath
type(request.ownership_expectation) is TrustedOwnershipExpectation
```

It also structurally validates the nested facts: `concrete_path.concrete_path`
has exact type `str`; `ownership_expectation.expected_uid` and
`ownership_expectation.expected_gid` each have exact type `int` and are
non-negative. Missing attributes, `bool`, subclasses, and other malformed
values fail validation. No `int(...)`, `str(...)`, `Path(...)`, `expanduser`,
normalization, canonicalization, or fallback is permitted.

An invalid or malformed request is an exception and fail-closed pre-I/O
condition, not a filesystem snapshot outcome. Its filesystem observation count
is exactly zero.

## 4. Exact target and observation owner

`MacFilesystemTargetMetadataSnapshotAdapter` in the future Mac adapter file is
the sole observation owner. It passes exactly this existing string, unchanged:

```text
os.lstat(request.concrete_path.concrete_path)
```

There is no `Path` conversion, join, strip, `normpath`, `abspath`, `realpath`,
resolve, `expanduser`, environment or `HOME` lookup, caller replacement,
alternate path, or candidate iteration. Mac AIControlCenter remains the sole
Control Plane. Ubuntu has zero role and zero authority.

## 5. Single-lstat observation budget

The filesystem observation budget per invocation is `0..1`. Invalid requests
cause zero observations. A valid request permits at most one logical call, the
exact `os.lstat(...)` call above. No result or exception permits a second
`lstat`.

The adapter performs no `os.stat`, `Path.stat`, `Path.lstat`, `exists`,
`lexists`, `is_dir`, `is_file`, `is_symlink`, parent walk, leaf lookup, retry,
fallback, reconnect, recovery, candidate iteration, directory enumeration,
`scandir`, `listdir`, `walk`, open, read, digest, or content acquisition.

## 6. Failure model

A definitive missing target, represented by `FileNotFoundError`, maps to:

```text
SOURCE_ABSENT -> ABSENT
```

Any other `OSError`, including inaccessible metadata, maps to:

```text
METADATA_ACCESS_FAILURE -> UNAVAILABLE
```

An ambiguous or malformed successful observation maps to:

```text
AMBIGUOUS_METADATA_RESULT -> UNCERTAIN
```

No exception branch retries, falls back, or causes another observation.

## 7. Observed metadata validation

The adapter consumes only `st_mode`, `st_uid`, and `st_gid` from the one
successful `lstat` result. It validates without coercion:

```text
type(st_mode) is int and st_mode >= 0
type(st_uid) is int and st_uid >= 0
type(st_gid) is int and st_gid >= 0
```

Thus `bool`, integer subclasses, `None`, strings, floats, missing attributes,
negative values, and all otherwise malformed values are rejected as
`AMBIGUOUS_METADATA_RESULT -> UNCERTAIN`, with no second observation.

## 8. Mode, type, and ownership policy

Classification uses only the `stat` module over the already-observed
`st_mode`. Positive directory metadata requires all of:

```text
not stat.S_ISLNK(st_mode)
stat.S_ISDIR(st_mode)
stat.S_IMODE(st_mode) == 0o700
st_uid == request.ownership_expectation.expected_uid
st_gid == request.ownership_expectation.expected_gid
```

Expected UID and GID come only from the already-issued nested ownership
expectation, which is structurally validated before `lstat`. The adapter does
not call `os.getuid`, `os.geteuid`, `os.getgid`, `os.getegid`, `pwd`, `grp`,
supplementary-group or ambient-process-group facilities, and it does not invoke
`issue_trusted_ownership_expectation`.

## 9. Deterministic classification order

Exactly one reason is selected in this order:

1. malformed observed metadata -> `AMBIGUOUS_METADATA_RESULT`;
2. `stat.S_ISLNK(st_mode)` -> `SYMLINK_REJECTED`;
3. not `stat.S_ISDIR(st_mode)` -> `WRONG_FILE_TYPE`;
4. `stat.S_IMODE(st_mode) != 0o700` -> `TARGET_MODE_MISMATCH`;
5. `st_uid != expected_uid` -> `TARGET_UID_MISMATCH`;
6. `st_gid != expected_gid` -> `TARGET_GID_MISMATCH`;
7. otherwise -> `DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`.

No classification step performs another filesystem call.

## 10. Exact result vocabularies

`FilesystemTargetMetadataSnapshotOutcome` has exactly:

```text
DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE
ABSENT
UNSAFE
UNAVAILABLE
UNCERTAIN
```

`FilesystemTargetMetadataSnapshotReason` has exactly:

```text
DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE
SOURCE_ABSENT
SYMLINK_REJECTED
WRONG_FILE_TYPE
TARGET_MODE_MISMATCH
TARGET_UID_MISMATCH
TARGET_GID_MISMATCH
METADATA_ACCESS_FAILURE
AMBIGUOUS_METADATA_RESULT
```

The canonical reason-to-outcome mapping is:

```text
DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE -> DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE
SOURCE_ABSENT -> ABSENT
SYMLINK_REJECTED -> UNSAFE
WRONG_FILE_TYPE -> UNSAFE
TARGET_MODE_MISMATCH -> UNSAFE
TARGET_UID_MISMATCH -> UNSAFE
TARGET_GID_MISMATCH -> UNSAFE
METADATA_ACCESS_FAILURE -> UNAVAILABLE
AMBIGUOUS_METADATA_RESULT -> UNCERTAIN
```

Neither enum reuses `SAFE_BOUND` or `METADATA_SAFE_AND_STABLY_BOUND`.

## 11. Target classification

The purely observational, zero-authority
`FilesystemTargetClassification` has the minimum exact vocabulary:

```text
UNOBSERVED
DIRECTORY
SYMLINK
OTHER
AMBIGUOUS
```

The canonical reason-to-classification relation is:

```text
SOURCE_ABSENT -> UNOBSERVED
METADATA_ACCESS_FAILURE -> UNOBSERVED
SYMLINK_REJECTED -> SYMLINK
WRONG_FILE_TYPE -> OTHER
TARGET_MODE_MISMATCH -> DIRECTORY
TARGET_UID_MISMATCH -> DIRECTORY
TARGET_GID_MISMATCH -> DIRECTORY
DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE -> DIRECTORY
AMBIGUOUS_METADATA_RESULT -> AMBIGUOUS
```

This vocabulary makes no safe, trusted, bound, verified, authorized, or stable
claim.

## 12. Snapshot value and fact semantics

`FilesystemTargetMetadataSnapshot` is immutable, slotted,
repository-classified, prohibits direct public construction, and grants zero
authority. Its exact discovered factual fields are:

```text
outcome: FilesystemTargetMetadataSnapshotOutcome
reason: FilesystemTargetMetadataSnapshotReason
target_classification: FilesystemTargetClassification
observed_mode: int | None
observed_uid: int | None
observed_gid: int | None
```

Its exact fixed non-claim fields are:

```text
stable_handle_bound: bool = False, init=False
toctou_closed: bool = False, init=False
fd_inode_device_bound: bool = False, init=False
```

It does not duplicate `expected_uid` or `expected_gid`. For a successful,
structurally valid `lstat`, the three observed fields contain exactly that
single observation's values without coercion. For `SOURCE_ABSENT` and
`METADATA_ACCESS_FAILURE`, all three are `None` because no metadata tuple was
observed. For `AMBIGUOUS_METADATA_RESULT`, all three are also exactly `None`;
the boundary does not retain partial values that could create misleading
partial safety meaning.

## 13. Positive result and TOCTOU non-claims

`DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE` means only that the single
point-in-time `lstat` tuple described a non-symlink directory at exact mode
`0700` whose UID and GID matched the expectation. It does not mean
`SAFE_BOUND`, `METADATA_SAFE_AND_STABLY_BOUND`, stable path binding, race
closure, file-descriptor binding, inode/device stability, content safety,
content acquisition, evidence admission, evidence verification, `RECOVER`
sufficiency, Production readiness, or Production authorization.

For every result, including the positive result:

```text
stable_handle_bound=false
TOCTOU_CLOSED=false
FD_INODE_DEVICE_BOUND=false
```

The differently capitalized contract labels above describe the same fixed
lowercase value fields and are always false.

## 14. Semantic separation and zero authority

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

No later boundary may infer authority from Python object identity. The request,
classification, and snapshot are factual values only. The snapshot is not
unforgeable provenance, authorization, a capability, admission evidence,
verification evidence, content-acquisition evidence, `RECOVER` sufficiency,
Production authorization, Production readiness, filesystem authority, or a
security boundary. Possession grants zero authority.

## 15. Governance and preserved program state

Mac AIControlCenter remains the sole Control Plane. Ubuntu has zero role and
zero authority. Governance and SEC-02 are unchanged,
`ControlledExecutionPort` remains uncoupled, and the mutation budget is zero.
No Production authorization semantics are introduced.

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

## 16. Next step

Only after final architecture read-only review and a separately authorized
implementation milestone may the exact proposed source and inert test files be
implemented. This contract does not authorize protected-source observation,
content acquisition, Production access, staging, commit, push, or activation.
