# SEC-02 Pre-Bootstrap Remediation Durable Attempt Journal

## SEC02-FS-MACRO-03B4R2-A provisioning contract

`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_PROVISIONING_AUTHORITY` is now repository
implemented as immutable plan/authorization models, exact-target validation,
and a fakeable adapter protocol. The target is fixed by the module, never by a
caller. The contract represents create-only provisioning and cannot represent
remediation, chmod/chown repair, arbitrary paths, recursion, deletion, reset, or
retry. Its purpose type is distinct from remediation authorization, so one
approval cannot satisfy both. No Production directory or journal was created;
operational readiness remains `NO`.

Native replay fingerprint derivation now matches the Python domain separator
and type-checks with an isolated module cache. It has not consumed a live
AuthorizationRef and is not operationally validated.

## SEC02-FS-MACRO-03B4R provisioning result

The root-owned evidence-store architecture and separate
`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_PROVISIONING_AUTHORITY` are defined. It is
exact-path and create-only, cannot authorize remediation, and cannot share one
approval with remediation. It remains unimplemented and not ready. The live
path was not inspected or created, so the journal remains non-operational.

Status: **REPOSITORY IMPLEMENTED; TEMP-PATH VALIDATED; NOT OPERATIONAL**

## Authority boundary

`PRE_BOOTSTRAP_REMEDIATION_ATTEMPT_JOURNAL` is a purpose-specific execution
evidence journal for only `GOVERNANCE_DIRECTORY_MODE_0755_TO_0700/V1`. It is
separate from the ordinary SEC-02 authorization-consumption database because
that database's governed directory is the unsafe remediation target. It is not
an issuer/bootstrap registry, Governance database, workflow store, retry or
rollback authority, feature state, or second Control Plane. Mac AIControlCenter
remains the sole Control Plane.

The frozen future path is:

`/Library/Application Support/AIControlCenter/Security/PreBootstrapRemediation/attempt-journal.sqlite3`

The repository adapter rejects that path and all non-temporary paths. This work
unit created no Production directory or database. Provisioning ownership and
authority remain unresolved; `JOURNAL_PROVISIONING_AUTHORITY_READY=NO`.

## Replay identity and minimized evidence

`AuthorizationReplayKey` is an immutable 64-character lowercase hexadecimal
SHA-256 digest over a fixed domain separator followed by exact non-empty
ephemeral capability bytes. Direct text construction is rejected. The native
input is never retained. The digest grants no authority and cannot recreate an
authorization capability. The contract does not assume undocumented entropy or
uniqueness in Apple's opaque external form: collisions safely deny a second
attempt, and live derivation remains unvalidated.

The journal stores only replay key, exact purpose/version, closed state, and
evidence timestamps. It cannot represent an `AuthorizationRef`, raw external
form, credential, password, username, authority-bearing token, command, argv,
environment, caller path/mode, or caller UID/GID.

`REPLAY_FINGERPRINT_CRYPTO_CONTRACT_DEFINED=YES`

`REPLAY_FINGERPRINT_OPERATIONALLY_VALIDATED=NO`

## Closed durable state machine

```text
ABSENT -> DURABLY_CLAIMED -> TERMINAL_SUCCESS
                           |  TERMINAL_FAILURE
                           |  TERMINAL_UNCERTAIN
```

The create-only unique claim commits before the intercepted helper call. Every
existing state denies another claim. A stranded durable claim after crash is
consumed evidence only: it grants no recovery execution or retry. There is no
claim stealing, lease, expiry, TTL retry, reset/delete API, rollback to absent,
automatic compensation, generic SQL input, or operator override.

SQLite schema version 1 uses parameterized create-only insertion, a strict state
check, exact purpose/version checks, a unique primary replay key, rollback
journaling, and `synchronous=FULL`; it uses neither UPSERT nor REPLACE nor WAL.
The isolated test directory/file contract is `0700`/`0600`. Schema mismatch,
unsafe object kind/mode, corrupt rows, unexpected existing rows, and storage
errors fail closed. Only a same-call ambiguous commit acknowledgement may
perform exact read-only reopen verification; it never retries a mutation.

Terminal-recording failure after helper invocation returns consuming
`UNCERTAIN`; the durable claim continues to deny replay. Existing ordinary
SEC-02 durable-consumption behavior is unchanged:
`CORE_SEMANTICS_CHANGE_REQUIRED=false`.

## Live readiness

Read-only review found zero valid code-signing identities, no native app bundle,
no helper identity, and no concrete mutual XPC signing requirements. Swift is
6.3.3 while the previously reviewed SDK module/toolchain mismatch remains
unresolved. Authorization Services still cannot independently prove fresh human
interaction, the replay fingerprint has no live validation, and Production
journal provisioning authority is absent. No host tooling, signing identity,
right, helper, or service was changed.

```text
PRE_BOOTSTRAP_REMEDIATION_JOURNAL_DEFINED=YES
PRE_BOOTSTRAP_REMEDIATION_JOURNAL_REPOSITORY_IMPLEMENTED=YES
PRE_BOOTSTRAP_REMEDIATION_JOURNAL_OPERATIONAL=NO
DURABLE_CLAIM_PRECEDES_HELPER_ATTEMPT=YES
DURABLY_CLAIMED_RECOVERY_EXECUTION_ALLOWED=NO
FAILURE_RETRY_ALLOWED=NO
UNCERTAINTY_RETRY_ALLOWED=NO
CLAIM_STEALING_ALLOWED=NO
LEASE_EXPIRY_RETRY_ALLOWED=NO
AUTHORIZATION_EXTERNAL_FORM_PERSISTED=NO
REPLAY_FINGERPRINT_CRYPTO_CONTRACT_DEFINED=YES
REPLAY_FINGERPRINT_OPERATIONALLY_VALIDATED=NO
JOURNAL_PROVISIONING_AUTHORITY_READY=NO
DURABLE_CRASH_SAFE_CONSUMPTION_OPERATIONAL=NO
LIVE_FRESH_APPROVAL_VERIFICATION_READY=NO
LIVE_PRIVILEGED_HELPER_OPERATIONAL=NO
PRODUCTION_REMEDIATION_AVAILABLE=NO
```

Validation recorded focused `52 passed`, related SEC-02 `302 passed`, and one
canonical run of `4408 passed, 5 deselected, 627 warnings`.
# 03B4R2-C provisioning durability update

Journal creation initializes a minimal completed receipt. Exact safe-existing state is read-only recognition; unsafe, ambiguous, or mismatching state fails closed. No authorization capability persists and no repair/retry/delete/recreate path exists.
