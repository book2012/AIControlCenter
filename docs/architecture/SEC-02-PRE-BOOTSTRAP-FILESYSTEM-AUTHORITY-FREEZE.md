# SEC-02 Pre-Bootstrap Filesystem Provisioning Authority Freeze

Status: **FROZEN — DEFINED, NOT IMPLEMENTED**

```text
SEC02_FS_01_PRE_BOOTSTRAP_TRUST_FILESYSTEM_PROVISIONING_AUTHORITY_FREEZE=COMPLETE
```

## 1. Decision and exact authority relation

The Mac Control Plane may eventually contain one purpose-bound
`PRE_BOOTSTRAP_CONTROL_PLANE_FILESYSTEM_PROVISIONING_AUTHORITY`. Its only
capability is one create-only attempt to establish the two fixed directories
required before SEC-02 Production trust bootstrap. This document defines that
authority; it does not implement, install, invoke, or operationally validate it.

The exact authority relation is:

```text
Pre-Bootstrap Filesystem Approver
  != Human Bootstrap Approver
  != prospective SEC-02 Human Issuer
  != ordinary SEC-02 Trusted Authorization Intake
  != SEC-02 bootstrap registry creator
  != Release Authority
  != Mac Release Installation Authority
  != ControlledExecutionPort
  != feature execution
  != WU09
  != Ubuntu
  != Docker/Colima
  != caller-selected generic executor
```

The approver authorizes only the fixed filesystem operation. The future
purpose-built Mac component verifies and consumes that approval and performs at
most one bounded attempt. Approval, operator, verifier, and mutation boundary
are separate roles. The authority is not a Governance authority, SEC-02 issuer,
bootstrap authority, installer, generic privileged helper, or executor.

## 2. Independent, non-circular authorization

The smallest permitted pre-SEC-02 authorization mechanism is a dedicated
macOS Authorization Services right, named and configured solely for this
operation, requiring fresh interactive authentication by a human administrator
acting as the **Pre-Bootstrap Filesystem Approver**. A cached generic right,
mere membership observation, current login, session unlock, UID/GID, filesystem
possession, or successful process launch is insufficient. The future
implementation must request the dedicated right immediately before its sole
attempt, reject preauthorization and right sharing, bind the returned grant to
the requesting purpose-built process and current ceremony, and destroy the
authorization reference after the attempt.

The dedicated right is an OS trust boundary that exists independently of the
absent generic SEC-02 issuer registry. It does not authenticate through the
prospective issuer, Human Bootstrap Approver, bootstrap approval, Release
Authority approval, release-install approval, feature authorization, or any
caller-provided credential. The human administrator may not be the prospective
issuer or Human Bootstrap Approver for the same SEC-02 initialization ceremony;
the future ceremony must record and verify that separation before mutation.

One fresh approval authorizes exactly one invocation and at most one bounded
filesystem create attempt. Success, known failure, uncertain outcome, process
exit, or loss of the authorization reference consumes the grant. There is no
automatic retry, rollback, repair, claim stealing, recovery, approval reuse,
or transfer to another process or operation. A later attempt requires a new
interactive approval and a fresh read-only evaluation from the beginning.

This closes the dependency boundary at architecture level:

```text
TRUST_DIRECTORY_CREATION_REQUIRES_EXISTING_SEC02_ISSUER=NO
TRUST_BOOTSTRAP_DEPENDENCY_CYCLE=NO
```

It does not claim that the dedicated right or purpose-built component exists.

## 3. Fixed filesystem contract

The operation has no path input. Its complete governed directory set is:

```text
<trusted_passwd_home>/Library/Application Support/AIControlCenter/governance
<trusted_passwd_home>/Library/Application Support/AIControlCenter/governance/trust
```

Each governed directory must be a real directory with exact mode `0700` and
exact UID/GID from the bound Darwin passwd record. The operation may create an
absent governed directory only with those final facts.

The shared parent:

```text
<trusted_passwd_home>/Library/Application Support/AIControlCenter
```

is a traversal prerequisite, not a newly protected trust directory. An
existing real parent is acceptable when it has the exact bound UID/GID, is not
group/world writable, and has safe mode `0755` as permitted by current policy.
This freeze does not reclassify it as `0700`, change it, or grant authority to
create it. Any missing, unsafe, symlinked, ambiguous, or incorrectly owned
prerequisite ancestor fails closed. There is no recursive normalization.

The registry leaf `sec02-human-issuers.v1.json`, the authorization-consumption
database, and every other file or directory are outside the mutation set.

The current governance directory was operationally observed as mode `0755`.
That value is an observation of the current host, not a permanent architecture
constant or an allowed alternative mode. Because governed directories require
exact mode `0700`, the observed governance directory is `UNSAFE_EXISTING`.
Create-only v1 must fail closed and has no chmod, chown, repair, replacement,
or other remediation authority. No mutation of that observed object is
authorized by this freeze.

## 4. Create-only state semantics

Version 1 is strictly **CREATE-ONLY**. For each governed directory, using a
single descriptor-bound observation:

```text
ABSENT         -> bounded create may be eligible
SAFE_EXISTING  -> read-only verify; no mutation
UNSAFE_EXISTING -> fail closed; no mutation
AMBIGUOUS      -> fail closed; no mutation
```

`SAFE_EXISTING` means a real, no-follow directory with exact bound-passwd
UID/GID and exact mode `0700`. `UNSAFE_EXISTING` includes a symlink, non-
directory, wrong owner, wrong group, or wrong mode. `AMBIGUOUS` includes races,
I/O uncertainty, inability to prove descriptor identity, or an unsupported
safety primitive.

The `trust` directory is considered only after the `governance` directory has
been safely verified or created and durably acknowledged. If the operation
creates `governance` and then cannot prove the eligibility or result of creating
`trust`, it reports a failed or uncertain consumed outcome and does not remove,
chmod, chown, or otherwise roll back `governance`. Repair requires a separately
frozen authority; none exists here.

## 5. Closed mutation language

The only allowed mutations are:

1. create the absent fixed `governance` directory with mode `0700`; and
2. create the absent fixed `trust` child directory with mode `0700`.

Both use expected ownership from the bound passwd record. The interface exposes
no arbitrary path, path fragment, leaf name, mode, UID, GID, username, command,
executable, shell text, argv, environment, working directory, subprocess, API
payload, or JSON mutation field.

The following are expressly prohibited:

- registry-leaf or authorization-database creation;
- arbitrary file or directory creation;
- recursive `mkdir` outside the exact contract;
- chmod, chown, ownership repair, permission repair, deletion, replacement,
  rename, cleanup, or normalization of an existing object;
- shell, generic command execution, caller-injected subprocesses, or network;
- Docker/Colima, Ubuntu, AWS, MDM, software installation, or application
  installation;
- anti-rollback receipt or Continuity Witness mutation;
- Keychain, Secure Enclave, key, signature, or trust-material mutation;
- SEC-02 issuer registration, bootstrap registry creation, authorization
  consumption, Production feature mutation, or `ControlledExecutionPort` use.

## 6. Path and ownership authority

The sole identity and home binding is:

```text
ruid == euid
-> non-root
-> pwd.getpwuid(bound_uid)
-> trusted passwd home, exact UID, exact GID
```

The bound Darwin passwd record is the only authority for the home and ownership
facts. `HOME`, `Path.home()`, environment, argv, API, JSON, a caller path,
username, UID, GID, platform value, or filesystem possession is never
authoritative. The interactive administrator approval authorizes the operation;
it does not select or replace the bound target identity.

```text
TRUST_OWNERSHIP_AUTHORITY=BOUND_DARWIN_PASSWD_RECORD
SEPARATE_UID_GID_AUTHORITY_REQUIRED=NO
CALLER_UID_GID_AUTHORITY_ALLOWED=NO
```

## 7. Filesystem safety and durability

The future implementation must operate on Darwin with descriptor-relative,
no-follow traversal. It opens and validates each prerequisite component without
following symlinks, retains the validated parent descriptor, and creates each
fixed child relative to that descriptor with create-if-absent semantics. It
must not re-resolve an absolute or parent pathname after descriptor validation.
Every existing or newly created governed object is verified through the bound
descriptor for directory type, inode/device continuity, exact ownership, and
exact mode.

Creation must use exclusive semantics and an explicit `0700` mode independent
of process umask. A preexisting leaf is never adopted as the result of a create
race; it is reclassified read-only and succeeds only if independently proven
`SAFE_EXISTING`, otherwise the operation fails closed. No unsupported Darwin
primitive is assumed: ordinary descriptor-relative Darwin `open`/`mkdirat`/
`fstatat`-class operations with no-follow checks are sufficient if the future
implementation proves the required invariants; inability to do so denies.

After each successful directory creation, the implementation must `fsync` the
created directory and its containing directory, then verify the postcondition
read-only. Unsupported durability, ambiguous acknowledgement, or postcondition
mismatch is a terminal uncertain consumed outcome. It grants no retry, cleanup,
rollback, or repair authority.

## 8. Relationship to later phases

The mandatory phase chain is:

```text
Pre-Bootstrap Filesystem Provisioning
-> read-only filesystem validation
-> Release/Anti-Rollback trust source operationalization
-> one-time SEC-02 registry bootstrap
-> ordinary Trusted Authorization Intake
-> Authorization Consumption Store
-> feature-specific SEC-02 mutation
```

Each arrow is a prerequisite boundary, not delegated authority. Filesystem
provisioning neither proves nor authorizes any later phase. In particular it
does not create the registry leaf or consumption store, approve bootstrap,
operationalize a release, admit an issuer, consume an authorization, or invoke
a feature. The bootstrap remains unable to create or repair the trust
directory, and the Mac Release Installation Authority remains unable to create
a generic trust directory.

## 9. Implementation boundary and smallest next Work Unit

No provisioning component, dedicated Authorization Services right, entitlement,
helper, schema, or test is added by this freeze. Production bootstrap remains
unavailable and no trusted issuer is operational.

The one smallest repository implementation Work Unit is:

```text
SEC02_FS_02_IMPLEMENT_PURE_PRE_BOOTSTRAP_FILESYSTEM_PLAN_AND_VALIDATOR
```

It should add only a side-effect-free Darwin identity/path planner and read-only
descriptor-policy validator for the fixed directory contract, with unit tests
for `ABSENT`, `SAFE_EXISTING`, `UNSAFE_EXISTING`, and `AMBIGUOUS`. It must not
request Authorization Services approval or create, chmod, chown, delete, or
otherwise mutate any filesystem object. This Work Unit is identified, not begun.
It can confirm the current governance directory as `UNSAFE_EXISTING`, but it
cannot operationally unblock the current host. If it confirms that
classification, a separate later remediation authority review and
implementation is required. This freeze neither defines nor authorizes that
remediation authority.

## 10. Review gates

```text
SEC02_FS_01_GATE=PASS
ARCHITECT_REVIEW=PASS
SEC02_FS_01_ARCHITECTURE_REVIEW=PASS
SEC02_FS_01_DOCUMENTATION_CONTENT_REVIEW=PASS

PRE_BOOTSTRAP_FS_AUTHORITY_DEFINED=YES
PRE_BOOTSTRAP_FS_AUTHORITY_IMPLEMENTED=NO
PRE_BOOTSTRAP_FS_AUTHORITY_OPERATIONALLY_VALIDATED=NO
CREATE_ONLY=YES

CURRENT_GOVERNANCE_DIRECTORY_OBSERVED_MODE=0755
CURRENT_GOVERNANCE_DIRECTORY_CLASSIFICATION=UNSAFE_EXISTING
CREATE_ONLY_AUTHORITY_CAN_REMEDIATE_CURRENT_GOVERNANCE_DIRECTORY=NO
CURRENT_PRE_BOOTSTRAP_FILESYSTEM_OPERATIONAL_GATE=BLOCKED_REMEDIATION_REQUIRED

TRUST_DIRECTORY_CREATION_AUTHORITY_DEFINED=YES
TRUST_DIRECTORY_CREATION_IMPLEMENTED=NO
TRUST_DIRECTORY_CREATION_REQUIRES_EXISTING_SEC02_ISSUER=NO
TRUST_BOOTSTRAP_DEPENDENCY_CYCLE=NO

BOOTSTRAP_MAY_CREATE_TRUST_DIRECTORY=NO
BOOTSTRAP_MAY_REPAIR_TRUST_DIRECTORY=NO
MAC_RELEASE_INSTALLATION_AUTHORITY_MAY_CREATE_GENERIC_TRUST_DIRECTORY=NO

GENERIC_EXECUTOR_ALLOWED=NO
ARBITRARY_PATH_ALLOWED=NO
ARBITRARY_CHMOD_ALLOWED=NO
ARBITRARY_CHOWN_ALLOWED=NO

GOVERNANCE_DIRECTORY_REQUIRED_MODE=0700
TRUST_DIRECTORY_REQUIRED_MODE=0700
REGISTRY_LEAF_CREATION_AUTHORITY_CHANGED=NO

PRODUCTION_BOOTSTRAP_AVAILABLE=NO
SEC02_TRUSTED_ISSUER_OPERATIONAL=NO

SEC02_SEMANTICS_CHANGED=false
GOVERNANCE_CORE_CHANGED=false
CONTROLLED_EXECUTION_PORT_CHANGED=false
WU09_FILES_CHANGED=false

PRODUCTION_ACCESS_PERFORMED=false
PRODUCTION_MUTATION_PERFORMED=false
PRODUCTION_AUTHORIZATION_CONSUMED=false
FILESYSTEM_MUTATION_PERFORMED=false
CANONICAL_RERUN_REQUIRED=NO

NEXT_WU=SEC02_FS_02_IMPLEMENT_PURE_PRE_BOOTSTRAP_FILESYSTEM_PLAN_AND_VALIDATOR
```
