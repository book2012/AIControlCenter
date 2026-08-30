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
PRODUCTION_REMEDIATION_AVAILABLE=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
SEC02_TRUSTED_ISSUER_OPERATIONAL=NO
```
