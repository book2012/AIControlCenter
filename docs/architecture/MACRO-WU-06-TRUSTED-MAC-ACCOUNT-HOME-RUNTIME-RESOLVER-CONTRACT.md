# MACRO-WU-06 Trusted Mac Account-Home Runtime Resolver Architecture Contract

## Status and scope

`ARCHITECTURE_DISCOVERY_GATE=PASS` and
`RUNTIME_RESOLUTION_BOUNDARY_REQUIRED=YES`. This architecture-only contract
freezes a future runtime resolution boundary. It does not implement or execute
the resolver, observe the platform or process UIDs, perform a passwd lookup,
establish a trusted home value, compose a path, or inspect the filesystem.

`TrustedMacAccountHomePolicy` is already implemented and closed. Its frozen
policy remains Darwin-only, rejects root, takes the real UID from `os.getuid()`
and the effective UID from `os.geteuid()`, requires equality, binds that equal
UID, and defines `pwd.getpwuid(bound_uid).pw_dir` as the account-home lookup
rule.

## Ordered fail-closed runtime boundary

A future implementation must execute exactly this order:

1. Observe the platform exactly once using `platform.system()`.
2. Require the exact returned value `Darwin`.
3. Fail closed before UID observation if platform observation or Darwin validation fails.
4. Observe `os.getuid()` exactly once.
5. Observe `os.geteuid()` exactly once.
6. Establish no bound identity until both observations succeed.
7. Reject root if either UID is 0.
8. Require equality.
9. Fail closed before passwd lookup on mismatch.
10. Bind equal UID as `bound_uid`.
11. Execute exactly one `pwd.getpwuid(bound_uid)` lookup.

After that ordered boundary, any lookup failure fails closed. No retry,
fallback, alternate account lookup, or `getpwnam` is permitted. No caller,
environment, or argv identity or home input is accepted.

No bound identity exists after only one UID observation or after either UID
observation fails. No passwd lookup may precede successful platform, non-root,
and UID-equivalence validation.

```text
PLATFORM_OBSERVATION_SOURCE=platform.system()
PLATFORM_OBSERVATION_COUNT_MAX=1
REAL_UID_OBSERVATION_COUNT_MAX=1
EFFECTIVE_UID_OBSERVATION_COUNT_MAX=1
PASSWD_LOOKUP_COUNT_MAX=1
RETRY_ALLOWED=false
FALLBACK_ALLOWED=false
RECONNECT_ALLOWED=false
RECOVERY_ALLOWED=false
```

## Exact passwd home validation

The single passwd result must provide `pw_dir`. That value must be a string,
must be non-empty, must contain no NUL, and must be lexically absolute as a
POSIX path. A validation failure fails closed.

The validated string must be preserved unchanged. The resolver must not strip,
expand, normalize, resolve, apply `realpath`, canonicalize, `stat`, `lstat`,
test `exists` or `is_dir`, inspect symlinks, owner, group, or mode, enumerate
paths, or otherwise probe filesystem state. Lexical POSIX absoluteness is value
validation only; it establishes no filesystem fact.

`HOME`, `Path.home()`, `expanduser`, caller home/path, argv home/path, fallback,
enumeration, candidate iteration, alternate account lookup, and `getpwnam` are
rejected authority.

## Zero-authority output concept

`ResolvedTrustedMacAccountHome` is the frozen output concept: an immutable,
slotted, zero-authority value object containing exactly two data fields:
`bound_uid` and `passwd_home`, the validated, unchanged passwd-derived home
string. Normal or direct supported construction is prohibited; the supported
construction path is successful construction by `RuntimeHomeResolver` after
the ordered validation above.

Python object-model mechanisms allow another in-process caller to bypass normal
construction in theory. The object therefore is not an unforgeable provenance
token, authorization token, capability, admission token, verification evidence,
or security boundary. Its possession or identity grants zero authority and
does not itself prove that the supported resolver path was used.

It does not prove filesystem existence, directory type, symlink safety,
UID/GID ownership, mode safety, metadata safety, protected-source existence or
safety, content acquisition, evidence admission or verification, `RECOVER`
sufficiency, Production authorization, or Production readiness.

Every later security-sensitive boundary must independently validate all
evidence and authority that it requires. This object is not sufficient evidence
for `RECOVER` or for any Production decision.

## Required semantic separation

```text
TrustedMacAccountHomePolicy
!= RuntimeAccountIdentityObservation
!= RuntimeHomeResolver
!= ResolvedTrustedMacAccountHome
!= AuthoritativeMacProtectedEvidenceSuffixPolicy
!= ProtectedEvidenceSuffix
!= ConcreteProtectedEvidencePath
!= SourceExistence
!= MetadataInspection
!= MetadataSafety
!= ContentAcquisition
!= Admission
!= Verification
!= Authority
```

The output cannot authorize suffix composition, concrete-path creation,
filesystem access, protected-source access, Production access, or any later
evidence operation. A desired-state package is not activation authorization.

## Ownership and governance

Mac AIControlCenter remains the sole Control Plane. Ubuntu has no resolver role
and zero authority. Governance core and SEC-02 remain unchanged.
`ControlledExecutionPort` is not coupled. This contract grants no execution,
mutation, filesystem, MariaDB, SQL, Docker/Colima, Ubuntu, protected-source, or
Production authority.

## Preserved program state

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
