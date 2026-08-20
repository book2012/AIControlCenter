# MACRO-WU-06 Trusted Mac Account-Home Policy Architecture Contract

## Status and scope

This architecture-only work unit freezes the trusted Mac account-home policy
boundary used by future protected external evidence path composition.
`TRUSTED_ACCOUNT_HOME_POLICY_LAYER_REQUIRED=true` and
`TRUSTED_ACCOUNT_HOME_ARCHITECTURE_EVIDENCE=SUFFICIENT_TO_FREEZE`.

The future implementation names may be `TrustedMacAccountHomePolicy` and
`TrustedMacAccountHomePolicyIdentity`. They are proposals only. This contract
does not execute an account lookup, implement a resolver, establish a trusted
home value, compose an absolute path, inspect the filesystem, or access a
protected source or Production.

## Fail-closed process identity policy

The platform must be Darwin and root is rejected. The real UID is obtained from
`os.getuid()`; the effective UID is obtained from `os.geteuid()`. They must be
equal. That single equal UID is bound as the account identity. Only a future
runtime implementation may apply this account-home lookup rule:

```text
pwd.getpwuid(bound_uid).pw_dir
```

This rule is architecture, not an executed lookup. In particular, `os.getuid()`
means the real UID, never the effective UID.

```text
PLATFORM_REQUIREMENT=Darwin
ROOT_ACCOUNT_ALLOWED=false
REAL_UID_SOURCE=os.getuid()
EFFECTIVE_UID_SOURCE=os.geteuid()
UID_EQUIVALENCE_REQUIRED=true
ACCOUNT_IDENTITY_BINDING=REAL_UID_EQUALS_EFFECTIVE_UID
ACCOUNT_HOME_LOOKUP_RULE=pwd.getpwuid(bound_uid).pw_dir
```

## Rejected authority and discovery

`HOME`, `Path.home`, `expanduser`, caller-selected home or path, and argv home
or path input are not authority. There is no fallback, enumeration, or candidate
iteration. Existing Governance path policies, the operational bootstrap
resolver, Shopping `control_plane_home` injection, and runtime `Path.home` or
`HOME` conventions are design evidence only and do not become authority here.

```text
HOME_ENVIRONMENT_AUTHORITY_ALLOWED=false
PATH_HOME_AUTHORITY_ALLOWED=false
EXPANDUSER_AUTHORITY_ALLOWED=false
CALLER_HOME_AUTHORITY_ALLOWED=false
CALLER_PATH_AUTHORITY_ALLOWED=false
ARGV_HOME_AUTHORITY_ALLOWED=false
ARGV_PATH_AUTHORITY_ALLOWED=false
FALLBACK_ALLOWED=false
ENUMERATION_ALLOWED=false
CANDIDATE_ITERATION_ALLOWED=false
```

## Required separation and suffix relationship

```text
ProtectedExternalEvidenceBaseLocationIdentity
!= AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity
!= AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity
!= exact protected-evidence suffix
!= TrustedMacAccountHomePolicyIdentity
!= process UID identity
!= passwd account-home lookup rule
!= runtime account-home resolver
!= trusted home value
!= absolute path
!= concrete protected-evidence path
!= source existence
!= metadata inspection
!= metadata safety
!= content acquisition
!= admission
!= verification
!= authority
```

The exact suffix remains
`Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity`.
It remains relative to a future trusted Mac account-home value. This contract
does not compose it with any home value.

## Authority and Control Plane boundary

This contract grants zero authorization, capability, execution, filesystem,
protected-source, Production, acquisition, admission, verification, MariaDB,
SQL, Docker/Colima, or Ubuntu authority. Mac AIControlCenter remains the sole
Control Plane. Ubuntu remains stateless and owns no AI workload, business logic,
application state, or Control Plane authority. Governance and SEC-02 remain
separate and unchanged. `ControlledExecutionPort` is not used or coupled.

## Frozen facts

```text
TRUSTED_ACCOUNT_HOME_POLICY_LAYER_REQUIRED=true
TRUSTED_ACCOUNT_HOME_ARCHITECTURE_EVIDENCE=SUFFICIENT_TO_FREEZE
RUNTIME_HOME_RESOLVER_AVAILABLE=false
TRUSTED_HOME_VALUE_ESTABLISHED=false
ABSOLUTE_PATH_ESTABLISHED=false
CONCRETE_PATH_VALUE_ESTABLISHED=false
FILESYSTEM_IO_PERFORMED=false
PROTECTED_SOURCE_ACCESS=NOT_PERFORMED
PRODUCTION_ACCESS=NOT_PERFORMED
RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT
RECOVER_EVIDENCE_SUFFICIENT=false
SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```
