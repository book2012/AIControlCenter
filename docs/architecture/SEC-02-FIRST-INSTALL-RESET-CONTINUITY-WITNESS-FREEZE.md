# SEC-02 First-Install Reset Continuity Witness Architecture Freeze

## 1. Status and scope

This document freezes architecture only for a purpose-bound Continuity Witness
Authority. It does not authorize implementation, deployment, Production access,
Production mutation, or activation. It does not select an implementation vendor,
protocol, hosting environment, or cryptographic primitive.

This freeze preserves SEC-02 semantics, Governance core,
`ControlledExecutionPort`, and WU09 unchanged. The Mac mini M4 remains the
always-on Brain and single Control Plane. Ubuntu remains an optional stateless
infrastructure worker with zero Control Plane authority.

## 2. Authoritative current state

```text
SEC02_FIRST_INSTALL_RESET_CONTINUITY_ANCHOR_DISCOVERY_GATE=BLOCKED_RESET_ANCHOR_UNDEFINED
NON_CIRCULAR_PERSISTENT_ANCHOR_CURRENTLY_PROVEN=NO
LOCAL_STATE_ABSENCE_PROVES_FIRST_INSTALL=NO
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
FIRST_INSTALL_REQUIRES_NON_CIRCULAR_PERSISTENT_ANCHOR=YES

PERSISTENT_ANCHOR_ROLE=CONTINUITY_AND_ELIGIBILITY_EVIDENCE_ONLY
PERSISTENT_ANCHOR_MAY_GRANT_INSTALL_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_SEC02_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_EXECUTION_AUTHORITY=NO

RECEIPT_CRYPTOGRAPHIC_AUTHENTICATION_REQUIRED=YES
RECEIPT_CRYPTOGRAPHIC_PRIMITIVE_DEFINED=NO
SOFTWARE_CRYPTO_FALLBACK_AUTHORIZED=NO

RELEASE_VERSION_STRICTLY_MONOTONIC=YES
TRUST_SOURCE_VERSION_NONDECREASING=YES
TRUST_SOURCE_CONTENT_CHANGE_REQUIRES_VERSION_INCREMENT=YES
SAME_RELEASE_VERSION_DIFFERENT_ARTIFACT_ALLOWED=NO

SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY
BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
```

## 3. Selected authority architecture

A new purpose-bound **Continuity Witness Authority** exists outside the governed
application state of the Mac. It owns durable continuity history used only to
produce continuity and eligibility evidence.

The Continuity Witness Authority:

- is not a Control Plane;
- is not an executor;
- is not SEC-02;
- is not Release Authority;
- grants zero Production mutation authority.

The following authorities and components are distinct and must not be collapsed,
co-hosted by implication, or treated as mutually substitutable:

```text
Continuity Witness Authority
!= Release Authority
!= Human Bootstrap Approver
!= prospective SEC-02 issuer
!= local operator
!= Mac Release Installation Authority
!= SEC-02 intake
!= ControlledExecutionPort
!= WU09
!= Ubuntu
```

The witness is outside Mac application-accessible governed state for the purpose
of continuity survival. Its durable history cannot be reset by deleting or
replacing any Mac application-accessible receipt, key, journal, evidence, bundle,
Keychain state, LaunchDaemon state, repository state, or filesystem state.

```text
CONTINUITY_WITNESS_ROLE=CONTINUITY_AND_ELIGIBILITY_EVIDENCE_ONLY
CONTINUITY_WITNESS_IS_CONTROL_PLANE=NO
CONTINUITY_WITNESS_MAY_GRANT_INSTALL_AUTHORITY=NO
CONTINUITY_WITNESS_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO
CONTINUITY_WITNESS_MAY_GRANT_SEC02_AUTHORITY=NO
CONTINUITY_WITNESS_MAY_GRANT_EXECUTION_AUTHORITY=NO
CONTINUITY_WITNESS_MAY_GRANT_RETRY_AUTHORITY=NO
CONTINUITY_WITNESS_MAY_GRANT_ROLLBACK_AUTHORITY=NO
```

## 4. Durable continuity record

For each enrolled host, the witness record must minimally bind:

- immutable `continuity_host_id`;
- enrollment generation;
- enrollment state;
- highest accepted `release_version`;
- highest accepted `bootstrap_trust_source_version`;
- previous accepted transition digest;
- continuity record generation;
- recovery/reset status;
- cryptographic record digest and signature metadata.

The record must preserve the frozen version rules:

```text
RELEASE_VERSION_STRICTLY_MONOTONIC=YES
TRUST_SOURCE_VERSION_NONDECREASING=YES
TRUST_SOURCE_CONTENT_CHANGE_REQUIRES_VERSION_INCREMENT=YES
SAME_RELEASE_VERSION_DIFFERENT_ARTIFACT_ALLOWED=NO
```

A reset, reinstall, receipt deletion, local key deletion, journal deletion,
bundle deletion, filesystem replacement, OS reinstall, or ordinary operator
action must never reset or erase the witness continuity history.

## 5. Genesis and reset resistance

Local state absence is never proof of first install and never authorizes GENESIS.
The witness must never accept caller-selected GENESIS solely because local state
is absent.

GENESIS requires a separately frozen enrollment ceremony. After a host has ever
been enrolled:

```text
GENESIS_ALLOWED=NO
```

This remains true unless a separately governed destructive
decommission/re-enrollment architecture is later frozen. This document does not
define or authorize such an architecture.

Because host identity, enrollment, recovery, and witness implementation remain
undefined, this freeze does not claim that the first-install reset attack is
resolved.

## 6. Challenge-bound, replay-resistant evidence

Each read-only continuity evaluation must generate a fresh random challenge for
that evaluation. A witness response must be challenge-bound, signed, freshness-
bounded, and replay-resistant. The signed response must bind at least:

- challenge;
- `continuity_host_id`;
- continuity record generation;
- highest `release_version`;
- highest `bootstrap_trust_source_version`;
- eligibility classification;
- `issued_at`;
- `expires_at`;
- witness identity and key ID.

An old response must not be reusable for a new evaluation. A response with a
challenge mismatch, expired freshness window, invalid signature, unknown witness
identity/key ID, malformed binding, or uncertain verification result must not
establish eligible continuity.

Eligibility classifications are closed. The architecture recognizes only:

```text
GENESIS_ELIGIBLE
CONTINUITY_VALID
RECOVERY_REQUIRED
DECOMMISSIONED
UNAVAILABLE
MALFORMED
UNCERTAIN
```

Adding or reinterpreting a classification requires a later architecture freeze.
Only eligibility and freshness evidence is produced; no classification grants
install, bootstrap, SEC-02, execution, retry, rollback, or Production mutation
authority.

## 7. Authorization composition

Release transition authorization remains exclusively:

```text
Release Authority authorization
+ validated continuity evidence
+ bounded Mac Release Installation Authority
```

All three terms are required and retain their separate purposes. Continuity
evidence is a required precondition and is never authorization. It cannot replace,
mint, amplify, retry, roll back, or delegate either Release Authority
authorization or bounded Mac Release Installation Authority.

## 8. Deliberately unselected implementation

This architecture freeze does not select an online implementation vendor,
protocol, cloud host, or deployment topology. It specifically does not select
GitHub, Notion, Apple services, Keychain, Secure Enclave, NVRAM, or filesystem
state as the witness implementation.

Receipt cryptographic authentication remains required, while its primitive is
undefined and software fallback remains unauthorized:

```text
RECEIPT_CRYPTOGRAPHIC_AUTHENTICATION_REQUIRED=YES
RECEIPT_CRYPTOGRAPHIC_PRIMITIVE_DEFINED=NO
SOFTWARE_CRYPTO_FALLBACK_AUTHORIZED=NO
```

## 9. Required later freezes

A later **HOST IDENTITY / ENROLLMENT** architecture freeze must prove how
`continuity_host_id` is established and immutably associated with the intended
host without allowing a reset operator, local operator, reinstalling party, or
caller to invent a new host identity. That freeze must also define the GENESIS
enrollment ceremony and its authority separation.

A later recovery architecture freeze must define recovery eligibility, evidence,
authority separation, and ceremony without permitting recovery to become GENESIS
replay, continuity rollback, or implicit Production mutation authority.

A later implementation freeze must select and validate the witness realization,
protocol, cryptographic mechanisms, durability model, availability behavior, and
operational boundaries. Desired state or implementation readiness must never be
interpreted as activation authorization.

```text
CONTINUITY_HOST_IDENTITY_DEFINED=NO
CONTINUITY_HOST_IDENTITY_OPERATOR_SELECTABLE=NO
CONTINUITY_GENESIS_ENROLLMENT_DEFINED=NO
CONTINUITY_RECOVERY_CEREMONY_DEFINED=NO
CONTINUITY_WITNESS_IMPLEMENTATION_DEFINED=NO
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
IMPLEMENTATION_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
```

## 10. Preserved trust ownership

```text
TRUST_OWNERSHIP_AUTHORITY=BOUND_DARWIN_PASSWD_RECORD
SEPARATE_UID_GID_AUTHORITY_REQUIRED=NO
```

The Continuity Witness Authority does not alter, replace, or acquire trust
ownership authority.

## 11. Final review gates

| Gate | Frozen result | Review requirement |
|---|---|---|
| `SEC02_CONTINUITY_WITNESS_ARCHITECTURE_FREEZE_GATE` | `FROZEN_ARCHITECTURE_ONLY` | The purpose-bound witness architecture and its non-authoritative role are frozen; implementation is not authorized. |
| `RESET_SURVIVAL_MODEL_GATE` | `REQUIRED_NOT_IMPLEMENTED` | Witness history must survive all listed local deletion, replacement, reinstall, and ordinary operator actions. |
| `LOCAL_ABSENCE_AUTHORITY_GATE` | `DENIED` | Local state absence proves neither first install nor GENESIS eligibility and grants zero authority. |
| `CONTINUITY_WITNESS_AUTHORITY_SEPARATION_GATE` | `REQUIRED` | Every listed authority and component remains distinct from the witness. |
| `CHALLENGE_REPLAY_RESISTANCE_GATE` | `REQUIRED_NOT_IMPLEMENTED` | Every evaluation requires a fresh challenge and a signed, challenge-bound, freshness-bounded response. |
| `GENESIS_REPLAY_PREVENTION_GATE` | `REQUIRED_NOT_IMPLEMENTED` | A previously enrolled host cannot return to GENESIS absent a later separately governed destructive decommission/re-enrollment freeze. |
| `HOST_IDENTITY_GATE` | `BLOCKED_UNDEFINED` | A later freeze must establish non-operator-selectable immutable host identity. |
| `ENROLLMENT_CEREMONY_GATE` | `BLOCKED_UNDEFINED` | A later freeze must define GENESIS enrollment. |
| `RECOVERY_CEREMONY_GATE` | `BLOCKED_UNDEFINED` | A later freeze must define recovery without GENESIS replay or continuity rollback. |
| `MAC_CONTROL_PLANE_GATE` | `PASS_UNCHANGED` | Mac mini M4 remains the single Control Plane; the witness is not a Control Plane. |
| `UBUNTU_ZERO_AUTHORITY_GATE` | `PASS_UNCHANGED` | Ubuntu has zero witness, SEC-02, release, install, bootstrap, execution, or Control Plane authority. |
| `SEC02_SEMANTICS_CHANGED` | `false` | SEC-02 semantics are unchanged. |

## 12. Change and activity attestation

```text
SEC02_SEMANTICS_CHANGED=false
GOVERNANCE_CORE_CHANGED=false
CONTROLLED_EXECUTION_PORT_CHANGED=false
WU09_FILES_CHANGED=false
CANONICAL_RERUN_REQUIRED=NO
PRODUCTION_ACCESS_PERFORMED=false
PRODUCTION_MUTATION_PERFORMED=false
PRODUCTION_AUTHORIZATION_CONSUMED=false
DOCKER_RUNTIME_ACCESSED=false
GIT_MUTATION=false
```

`GIT_MUTATION=false` means no staging, commit, push, branch rewrite, or other Git
state mutation is authorized or performed by this freeze; the requested untracked
architecture document is a working-tree filesystem addition only.
