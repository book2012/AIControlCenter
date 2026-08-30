# SEC-02 Narrow Governance Directory Remediation Authority

Status: **DEFINED; REPOSITORY CONTRACT ONLY; NOT OPERATIONAL**

## Exact purpose and target

This authority is separate from the FS-01 create-only authority and is bound to
exactly `<trusted_passwd_home>/Library/Application Support/AIControlCenter/governance`.
The trusted home, UID, and GID come only from the non-root, equal real/effective
UID's Darwin passwd record. It has no caller-selected path, mode, UID, or GID.

Its only possible future mutation is mode `0755` to exact mode `0700`, leaving
the passwd-bound owner and group unchanged. The observed `0755` is current
operational evidence classified `UNSAFE_EXISTING`, not an allowed steady state.
The `trust` child is never a remediation target.

Eligibility requires one descriptor-bound observation proving a real directory,
no symlink, exact passwd UID/GID, and exact mode `0755`. Mode `0700` requires no
mutation. Any other mode, owner, group, object kind, target, race, I/O uncertainty,
unsupported primitive, or inability to prove descriptor identity denies.

## Closed authorization and mutation boundary

A future implementation requires a distinct purpose-specific macOS Authorization
Services right. One fresh interactive human approval permits one exact attempt.
Success, failure, or uncertainty consumes it. There is no automatic retry,
rollback, reuse, transfer, claim stealing, generic executor, or implied recovery.
This definition neither installs a right nor implements a Production adapter.

The authority explicitly denies arbitrary path or chmod; every mode except the
exact `0700` result; chown or owner/group repair; symlink repair; non-directory
replacement; delete; rename; recursion; trust-directory, registry, authorization
database, release, or bootstrap mutation; `ControlledExecutionPort`; Docker,
Colima, Ubuntu, AWS, and feature Production execution.

The Mac mini remains the sole Control Plane and Ubuntu has zero authority. The
absent SEC-02 registry cannot authorize this pre-registry operation. Remediation
approval grants no bootstrap, issuer, retry, release, or feature authority.

### SEC02-FS-MACRO-03A concrete authorization contract

The repository freezes a single dedicated right,
`com.aicontrolcenter.governance-remediation.mode-0755-to-0700`, for the single
purpose `GOVERNANCE_DIRECTORY_MODE_0755_TO_0700`. The right is not selected by
the caller and is not generic or shared. A qualifying representation must be a
fresh interactive approval: preauthorization, reuse, sharing, retry, and
recovery reuse are denied.

One accepted approval creates one payload-free available attempt. Its sole
valid transition is to claimed, and a claimed attempt must transition exactly
once to consumed with `SUCCESS`, `FAILURE`, or `UNCERTAIN`. Every result consumes
the approval. A claimed or consumed attempt cannot be claimed again; there is
no claim stealing, rollback authority, or automatic retry.

The authorization presentation, decision, and attempt convey no executable,
command, argv, environment, shell, subprocess, API payload, path, UID, GID, or
mode. Before authorization, the pure policy independently validates the exact
passwd-home-derived governance target, exact `0755` observed mode, exact `0700`
result mode, unchanged passwd UID/GID, and fixed remediation operation. The
`trust` child, registry/database targets, authorization database, chown, and all
bootstrap, issuer, release, feature, and execution authorities remain denied.

These are architecture-required semantics and are repository implemented as
immutable models and pure validation. Future SEC02-FS-MACRO-03B work must
separately validate actual macOS Authorization Services API behavior, right
installation/configuration, interactive acquisition, process/crash behavior,
and durable one-attempt consumption. This Work Unit makes no claim that those
operational properties are already supplied by an API, and it neither installs
nor invokes the right.

### SEC02-FS-MACRO-03B1 platform boundary

The local macOS SDK Authorization Services contract was reviewed for
`AuthorizationCreate`, `AuthorizationCopyRights`, `InteractionAllowed`,
`ExtendRights`, `PreAuthorize`, `DestroyRights`, and external forms.
`InteractionAllowed` permits interaction when required; it does not prove that
fresh interaction occurred. The repository therefore records fresh approval as
the closed vocabulary `VERIFIED`, `NOT_VERIFIABLE`, `DENIED`, `CANCELED`, or
`ERROR`, and only `VERIFIED` may reach the execution port. No current live
adapter can independently produce that evidence, so Production remains closed.

The repository now defines a zero-argument Authorization Services port and a
zero-argument privileged remediation port for the single fixed operation.
Intercepted adapters validate orchestration without an OS prompt, XPC request,
helper, or filesystem mutation. Authorization decision, execution capability,
execution attempt, and verified postcondition remain distinct. An adapter
exception, helper/process loss, invalid result, or missing postcondition is
`UNCERTAIN` and consuming; there is no automatic retry.

A future macOS 13+ helper boundary may use a bundled root LaunchDaemon managed
through `SMAppService`. It must independently derive the Darwin passwd target
and revalidate the exact descriptor-bound precondition and postcondition. It is
an execution adapter only, not a Control Plane. `SMJobBless` and
`AuthorizationExecuteWithPrivileges` are not selected. No native binding,
right installation, helper registration, helper start, or chmod exists in
03B1.

The current in-memory immutable state machine proves repository transition
semantics only. Production still requires a separately reviewed crash-safe
claim/consumption mechanism that cannot resurrect or reuse authority after
process or helper loss. It is not coupled to the unavailable ordinary SEC-02
authorization-consumption database.

## Repository implementation and operational status

The repository contains only immutable eligibility/plan/postcondition contracts,
a pure planner, and a future one-attempt port protocol. It contains no live chmod
adapter and invokes neither Authorization Services nor Production.

```text
SEC02_FS_02_IMPLEMENTED=YES
SEC02_FS_02_OPERATIONALLY_VALIDATED=NO
CURRENT_GOVERNANCE_DIRECTORY_OBSERVED_MODE=0755
CURRENT_GOVERNANCE_DIRECTORY_CLASSIFICATION=UNSAFE_EXISTING
NARROW_GOVERNANCE_REMEDIATION_AUTHORITY_DEFINED=YES
NARROW_GOVERNANCE_REMEDIATION_IMPLEMENTED=REPOSITORY_ONLY
NARROW_GOVERNANCE_REMEDIATION_PRODUCTION_ADAPTER_IMPLEMENTED=NO
NARROW_GOVERNANCE_REMEDIATION_OPERATIONALLY_VALIDATED=NO
CONCRETE_REMEDIATION_AUTHORIZATION_CONTRACT_DEFINED=YES
CONCRETE_REMEDIATION_AUTHORIZATION_CONTRACT_IMPLEMENTED=YES
AUTHORIZATION_SERVICES_API_CONTRACT_REVIEWED=YES
INTERACTION_ALLOWED_PROVES_FRESH_INTERACTION=NO
PREAUTHORIZATION_ALLOWED=NO
SHARED_AUTHORITY_ALLOWED=NO
AUTHORIZATION_EXECUTE_WITH_PRIVILEGES_ALLOWED=NO
SMJOBBLESS_SELECTED=NO
SMAPPSERVICE_FUTURE_BOUNDARY_SELECTED=YES
AUTHORIZATION_SERVICES_PORT_IMPLEMENTED=YES
PRIVILEGED_REMEDIATION_PORT_IMPLEMENTED=YES
FAKE_AUTHORIZATION_ADAPTER_IMPLEMENTED=YES
FAKE_PRIVILEGED_ADAPTER_IMPLEMENTED=YES
DURABLE_CRASH_SAFE_CONSUMPTION_OPERATIONAL=NO
AUTHORIZATION_SERVICES_INVOKED=NO
LIVE_CHMOD_ADAPTER_IMPLEMENTED=NO
PRODUCTION_REMEDIATION_AVAILABLE=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
SEC02_TRUSTED_ISSUER_OPERATIONAL=NO
```
