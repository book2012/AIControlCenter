# MACRO-WU-06 Concrete Protected-Evidence Filesystem Binding Architecture Contract

## Status and discovery

`ARCHITECTURE_DISCOVERY_GATE=PASS` and
`EXISTING_BOUNDARY_REUSE_GATE=PASS`.

Repository discovery found and reuses these closed semantics:

- `ConcreteProtectedEvidencePath` is an immutable lexical value with exactly
  `concrete_path`; possession and object identity establish no provenance,
  filesystem fact, security authority, or capability.
- protected-source profiles map one-to-one to four symbolic fixed source slots
  and then four symbolic concrete source-location identities. They are not
  filesystem paths and permit no caller slot/location selection.
- a protected parent is required to be a non-symlink directory at exact mode
  `0700`, owned by explicitly trusted UID and GID; a protected leaf is a later,
  separate regular non-symlink file no broader than `0600`.
- existing negative metadata concepts and reasons may be reused where their
  semantics match, including absence, symlink, wrong type, mode, UID/GID,
  instability/race, access failure, and ambiguity. The historical positive
  `SAFE_BOUND` / `METADATA_SAFE_AND_STABLY_BOUND` vocabulary is not reusable
  for this single-`lstat` snapshot because it is not stably bound.
- existing protected-source inspection uses `lstat`, rejects symlinks, and
  does not follow them. Existing contracts require future FD/inode binding and
  one-shot human-authorized acquisition; a pathname metadata snapshot cannot
  satisfy those later requirements.

The legacy `observe_fixed_protected_source` function is discovery evidence
only. It accepts a caller `Path`, inspects both parent and leaf, and is isolated
from the path-free protected-source metadata port. This contract does not
route through, widen, or reactivate it.

## Strict boundary separation

```text
ConcreteProtectedEvidencePath
!= TrustedOwnershipExpectation
!= FilesystemTargetMetadataSnapshot
!= SourceExistence
!= MetadataInspection
!= MetadataSafety
!= ContentAcquisition
!= EvidenceAdmission
!= EvidenceVerification
!= Authority
```

`ConcreteProtectedEvidencePath` remains zero-authority. Neither possession nor
Python object identity is provenance or security authority. The filesystem
metadata snapshot is a distinct future Mac adapter boundary. It may
structurally require one already supplied `ConcreteProtectedEvidencePath` and
explicit expected UID and GID, but arbitrary caller-selected UID/GID values are
not trusted ownership authority. It must not construct or execute
`RuntimeHomeResolver`, compose a path, or derive identity, path, or ownership
authority from `HOME`, environment, argv, a caller-selected path, ambient
UID/GID lookup, `os.getgid()`, or `os.getegid()`.

`TrustedOwnershipExpectation` is distinct from
`ConcreteProtectedEvidencePath`, `FilesystemTargetMetadataSnapshot`,
`MetadataSafety`, `ContentAcquisition`, and `Authority`. Possession of
`ConcreteProtectedEvidencePath` grants no ownership authority. Possession of
`ResolvedTrustedMacAccountHome` grants no security provenance and supplies no
trusted GID. Repository discovery has not established an authoritative
operational trusted-GID issuer, and this work neither invents one, extends
`RuntimeHomeResolver`, nor adds another `pwd` lookup. A positive operational
ownership-safe claim remains impossible until a separate trusted ownership
expectation boundary is architecture-frozen and implemented.

The caller supplies no replacement path, suffix, slot, candidate, alternate,
fallback, enumeration root, or retry policy. Exact target means the unchanged
`concrete_path` value and no other pathname. No normalization, resolution,
`realpath`, directory traversal, candidate iteration, or alternate lookup is
permitted.

## First and maximum filesystem observation

The future boundary uses **`lstat` only**. It performs at most one filesystem
observation total: exactly one `lstat` of the exact target when invoked, and
zero observations if request validation fails before I/O.

`stat` is prohibited because it follows a symlink and would erase the
repository-required non-symlink distinction. Ordered `lstat` then `stat` is
also prohibited here: it doubles the observation surface, follows a target
after a pathname race, and does not produce the FD/inode stability required by
later acquisition. The existing protected-source contract already establishes
`lstat`-based symlink rejection, so this freeze reuses it.

No parent walk, leaf lookup, `exists`, `is_dir`, `is_file`, `is_symlink`, open,
read, directory enumeration, second metadata check, retry, recovery, or
fallback is allowed. Filesystem observation count is therefore `0..1`; content
open/read/acquisition count is always `0`; mutation count is always `0`.

## Target identity and metadata safety

At this layer the exact target must be a regular directory identity in the
POSIX file-type sense (`S_ISDIR`), not a regular file. A symlink is rejected,
including a symlink whose referent is a directory. The single `lstat` snapshot
must show:

- directory type and not symlink;
- exact permission mode `0700`;
- `st_uid` equal to the explicitly supplied expected UID; and
- `st_gid` equal to the explicitly supplied expected GID.

The boundary makes no broader filesystem-type claim. In particular it does not
identify APFS, a local mount, a remote mount, a device class, mount options, or
filesystem durability. No repository contract currently freezes such a check,
and pathname `lstat` metadata does not establish it. Unsupported or ambiguous
metadata fails closed.

Regular-file identity, leaf mode no broader than `0600`, non-empty size, and
the four fixed source slots belong to later exact-leaf binding. They are not
asserted or inspected here.

## Snapshot result and error vocabulary

The future result is an immutable, slotted, zero-authority, point-in-time
metadata snapshot. Its distinct snapshot-level positive concept is
`DIRECTORY_METADATA_SNAPSHOT_ACCEPTABLE`. It must not use `SAFE_BOUND` or
`METADATA_SAFE_AND_STABLY_BOUND` as its positive classification. Applicable
existing negative concepts may be reused only where their semantics match,
including `ABSENT`, `UNSAFE`, `UNAVAILABLE`, `UNCERTAIN`, `SOURCE_ABSENT`,
`SYMLINK_REJECTED`, `WRONG_FILE_TYPE`, `PARENT_MODE_MISMATCH`,
`PARENT_UID_GID_MISMATCH`, `PATH_REPLACEMENT_RACE`,
`METADATA_ACCESS_FAILURE`, and `AMBIGUOUS_METADATA_RESULT`. Historical
`STABLY_BOUND` terminology is not reinterpreted as compatible with
`stable_handle_bound=false`.

Every result must preserve `stable_handle_bound=false`, `TOCTOU_CLOSED=false`,
and `FD_INODE_DEVICE_BOUND=false`. Construction or possession makes it neither
operational evidence nor authority.

Only a successful single snapshot may classify source existence, metadata
inspection, and directory metadata safety for this boundary. Absence is not
safety. Any exception, malformed request, unexpected metadata, ambiguity,
race indication, or classification contradiction fails closed and grants no
positive fact. No error authorizes retry, recovery, fallback, or another path.

The result grants no content acquisition, admission, verification, `RECOVER`
sufficiency, capability, authorization, mutation, Production, or execution
authority. It is not operational evidence merely because it exists or because
its request or path object has a particular identity.

## TOCTOU and later boundaries

One `lstat` is a point-in-time pathname snapshot. It cannot prevent replacement
after observation. This boundary therefore does not claim a stable live target,
open-file binding, or acquisition safety. Any later content acquisition must be
separately human-authorized, open without following symlinks, bind and validate
an FD/inode/device identity, and enforce its own one-shot policy. Those later
semantics are explicitly out of scope and are not authorized by this contract.

## Control Plane, mutation, and preserved state

Mutation budget is exactly `0`. Governance and SEC-02 semantics are unchanged,
and `ControlledExecutionPort` is not coupled. No content is opened or read. No
MariaDB, SQL, PyMySQL, Docker, Colima, Ubuntu, network, process, Production, or
protected-source access is performed by this architecture work.

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

## Next step

After architecture Git closeout, architecture-freeze and implement a separate
trusted ownership expectation boundary before any positive operational
ownership-safe claim. Only after that separate gate may a repository-only
metadata snapshot request/result and Mac `lstat`-only adapter be implemented,
with inert tests only and without executing the adapter against protected
evidence or Production.
