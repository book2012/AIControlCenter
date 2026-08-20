# MACRO-WU-06 Protected External Evidence Exact Suffix Architecture Contract

## Status and scope

This repository architecture decision resolves
`NO_REPOSITORY_OWNED_PROTECTED_EXTERNAL_EVIDENCE_SPECIFIC_EXACT_SUFFIX_CONTRACT`.
It establishes only the exact repository-owned suffix for a future authoritative
Mac protected-evidence path policy. It implements no Python type, runtime
resolver, filesystem operation, source access, metadata inspection, evidence
operation, or Production operation.

The next repository milestone is
`MACRO_WU_06_AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY_IMPLEMENTATION`.
That implementation is not part of this contract.

## Exact suffix decision

The exact suffix is:

```text
Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity
```

It is a relative suffix, not an absolute path. Its future composition model is:

```text
TRUSTED_MAC_ACCOUNT_HOME
+
Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity
```

`TRUSTED_MAC_ACCOUNT_HOME` is deliberately unresolved. This contract does not
implement or select a trusted Mac account-home resolver.

The future code identities are
`AuthoritativeMacProtectedEvidenceSuffixPolicy` and
`AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity`; their symbolic identity
is `AUTHORITATIVE_MAC_PROTECTED_EVIDENCE_SUFFIX_POLICY`. These names are
architecture proposals only and are not implemented by this work unit.

## Required separation

The architecture preserves this strict distinction:

```text
ProtectedExternalEvidenceBaseLocationIdentity
!= AuthoritativeMacProtectedEvidenceBasePathPolicyIdentity
!= AuthoritativeMacProtectedEvidenceSuffixPolicyIdentity
!= exact suffix value
!= runtime account-home resolution
!= concrete path
!= source existence
!= metadata inspection
!= metadata safety
!= content acquisition
!= admission
!= verification
!= authority
```

The suffix does not establish a concrete or absolute path, directory existence,
source existence, historical evidence existence, metadata inspection, metadata
safety, content acquisition, admission, verification, Production access,
authorization, or execution authority.

Existing governance paths, `.config/aicontrolcenter/shopping-secrets`, runtime,
build, or staging paths, WordPress or WooCommerce locations, and Ubuntu worker
paths are not inputs to this decision and acquire no authority from it.

## Closed path authority

No caller may choose or inject a base path, concrete path, or suffix. Environment
variables, including `HOME`, argv, fallback, path enumeration, and candidate
iteration are not path authority. The future resolver must compose the exact
repository-owned suffix only with a separately established trusted Mac
account-home result.

```text
CALLER_BASE_PATH_SELECTION_ALLOWED=false
CALLER_PATH_INJECTION_ALLOWED=false
CALLER_SUFFIX_INJECTION_ALLOWED=false
ENVIRONMENT_PATH_AUTHORITY_ALLOWED=false
HOME_ENVIRONMENT_AUTHORITY_ALLOWED=false
ARGV_PATH_AUTHORITY_ALLOWED=false
FALLBACK_ALLOWED=false
PATH_ENUMERATION_ALLOWED=false
CANDIDATE_ITERATION_ALLOWED=false
```

## Authority and Control Plane boundary

This contract grants zero authorization, capability, execution, mutation, retry,
reconnect, rollback, acquisition, admission, verification, Production-access,
protected-source-access, MariaDB, SQL, process, or Ubuntu authority. Mac
AIControlCenter remains the sole Control Plane. Ubuntu remains a stateless,
zero-authority infrastructure worker and owns no AI workload, business logic,
application state, or Control Plane authority.

Governance semantics and SEC-02 are unchanged. `ControlledExecutionPort` is not
reused or coupled. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

```text
authorization authority=false
capability authority=false
execution authority=false
mutation authority=false
retry authority=false
reconnect authority=false
rollback authority=false
acquisition authority=false
admission authority=false
verification authority=false
Production access authority=false
protected source access authority=false
MariaDB authority=false
SQL authority=false
process authority=false
Ubuntu authority=false
```

## Authoritative facts

```text
EXACT_SUFFIX_POLICY_LAYER_REQUIRED=true
EXACT_SUFFIX_POLICY_EVIDENCE=ESTABLISHED_BY_ARCHITECTURE_DECISION
EXACT_SUFFIX_VALUE_ESTABLISHED=true
EXACT_PROTECTED_EVIDENCE_SUFFIX=Library/Application Support/AIControlCenter/protected-external-evidence/mariadb-continuity
SUFFIX_IS_RELATIVE_TO_TRUSTED_ACCOUNT_HOME=true
ABSOLUTE_PATH_ESTABLISHED=false
CONCRETE_PATH_VALUE_ESTABLISHED=false
RUNTIME_HOME_RESOLVER_AVAILABLE=false
AUTHORITATIVE_BASE_LOCATION_ALREADY_EXISTS=false
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
MACRO_WU_06=IN_PROGRESS
REMAINING_AUTHORITATIVE_MACRO_WUS=7
AUTHORITATIVE_REMAINING_RANGE=WU06-WU12
```
