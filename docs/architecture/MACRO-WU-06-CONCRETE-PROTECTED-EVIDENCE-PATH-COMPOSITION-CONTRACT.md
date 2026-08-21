# MACRO-WU-06 Concrete Protected-Evidence Path Composition Architecture Contract

## Status, discovery, and scope

`ARCHITECTURE_DISCOVERY_GATE=PASS`. Repository discovery found these existing
authoritative components:

- `ResolvedTrustedMacAccountHome` and `RuntimeHomeResolver` in
  `core.secrets.mariadb_continuity_trusted_mac_account_home_runtime_resolver`;
  the resolved value has exactly `bound_uid` and unchanged `passwd_home`.
- `AuthoritativeMacProtectedEvidenceSuffixPolicy`,
  `AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity`, and
  `EXACT_PROTECTED_EVIDENCE_SUFFIX` in
  `core.secrets.mariadb_continuity_authoritative_mac_protected_evidence_suffix`.
- the inert Mac suffix-policy source projection in
  `ops.macos.shopping.mariadb_continuity_authoritative_mac_protected_evidence_suffix_source`.
- existing protected-evidence source-profile, fixed-source-slot, base-location,
  and concrete-source-location contracts. Those symbolic contracts remain
  distinct and supply no composed lexical path for this boundary.

This architecture-only decision freezes the future composition boundary:

```text
ResolvedTrustedMacAccountHome
+ repository-owned frozen exact protected-evidence suffix
-> ConcreteProtectedEvidencePath
```

It implements no type or composer, executes no resolver, composes no runtime
path, and establishes no filesystem or authority fact.

## Input and boundary separation

The composer consumes an already-existing `ResolvedTrustedMacAccountHome`. It
must not construct or execute `RuntimeHomeResolver` and must not observe
`platform.system()`, `os.getuid()`, `os.geteuid()`, or `pwd.getpwuid()`.
Resolution and composition remain separate boundaries.

```text
ResolvedTrustedMacAccountHome
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

The future supported composer accepts only the resolved-home value. It accepts
no caller-provided suffix, environment suffix, argv suffix, alternate suffix,
candidate suffix, fallback suffix, suffix enumeration, caller-provided base
path, or caller-provided concrete path.

## Exact suffix authority

The repository solely owns this exact relative suffix:

```text
Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity
```

No external component owns or may override this policy. The future composer
obtains the frozen value from the repository-owned suffix policy; it does not
expose suffix selection as an input.

## Exact lexical composition

Composition is string-only and deterministic. The exact rule is:

```text
if passwd_home ends with "/":
    concrete_path = passwd_home + exact_suffix
else:
    concrete_path = passwd_home + "/" + exact_suffix
```

The rule inserts at most one boundary separator. It does not otherwise alter
the passwd-derived home string or suffix. These examples are normative:

```text
passwd_home="/"
-> "/Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity"

passwd_home="/Users/trusted"
-> "/Users/trusted/Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity"

passwd_home="/Users/name/../unchanged"
-> "/Users/name/../unchanged/Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity"

passwd_home="//network-like"
-> "//network-like/Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity"
```

None of these values is normalized.

The composer must not use or perform `Path.home`, `expanduser`, `os.path.join`,
pathlib composition, `normpath`, `abspath`, `resolve`, `realpath`,
canonicalization, `strip`, `HOME` or other environment authority, argv
authority, alternate/candidate paths, retry, fallback, or enumeration. Explicit
string composition is required so hidden path transformation semantics cannot
enter this boundary.

## Absolutely no filesystem observation

The architecture work and future composer perform none of: open/read, exists,
`is_dir`, `is_file`, `is_symlink`, `stat`, `lstat`, owner/group/mode/symlink
inspection, directory enumeration, or any filesystem probing.
`ConcreteProtectedEvidencePath` is lexical only and establishes no filesystem
fact.

## Zero-authority value concept

`ConcreteProtectedEvidencePath` is a distinct immutable, slotted,
zero-authority value concept with the minimum shape of exactly one data field:
`concrete_path: str`. No UID, suffix, policy, authorization, capability,
admission, verification, Production authority, protected-source authority, or
filesystem authority is stored in it.

Its possession or identity grants zero authority. It is not an unforgeable
provenance token, authorization, capability, admission evidence, verification
evidence, `RECOVER` evidence sufficiency, filesystem existence or safety
evidence, Production authorization/readiness, or a security boundary. Python
object identity is not a security boundary. Every later security-sensitive
boundary independently validates all facts, evidence, and authority it needs.

## Control Plane and governance

Mac AIControlCenter is the sole Control Plane. Ubuntu has zero role and zero
authority in this boundary. Governance and SEC-02 are unchanged.
`ControlledExecutionPort` remains uncoupled. This contract grants no execution,
mutation, filesystem, protected-source, Production, MariaDB, SQL,
Docker/Colima, process, or Ubuntu authority.

## No runtime claim and preserved program state

This freeze does not compose a real path or execute any observation:

```text
RUNTIME_HOME_RESOLVER_AVAILABLE=true
RUNTIME_HOME_RESOLVER_REPOSITORY_VALIDATED=true
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

## Next boundary

Only after this architecture contract is Git-closed, the next local
submilestone is
`MACRO_WU_06_CONCRETE_PROTECTED_EVIDENCE_PATH_COMPOSITION_IMPLEMENTATION`.
That later implementation is repository-only and zero-authority and must still
perform no protected-source or Production access.
