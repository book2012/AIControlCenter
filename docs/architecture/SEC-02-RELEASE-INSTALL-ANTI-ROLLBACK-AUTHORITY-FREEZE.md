# SEC-02 Release-Install / Anti-Rollback Authority Architecture Freeze

Status: **FROZEN ARCHITECTURE; NOT IMPLEMENTED; NOT OPERATIONALLY VALIDATED**

```text
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_ARCHITECTURE_FROZEN=YES
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_IMPLEMENTED=NO
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_OPERATIONALLY_VALIDATED=NO
SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY
```

## 1. Decision and scope

This document freezes the next architecture milestone required by the already
frozen SEC-02 Bootstrap Approver Trust Source architecture. It defines the
only authority permitted to authenticate a Mac application release transition
and advance the Mac-local highest-accepted release and bootstrap trust-source
versions.

The selected boundary is a new, purpose-built **Mac Release Installation
Authority**. It is not an existing repository subsystem. Its future concrete
form is a narrowly scoped privileged macOS installation service, or an
equivalent macOS-native boundary proven to provide the same isolation. It may
only verify an authorized AIControlCenter release package, publish its complete
application bundle, advance the authenticated anti-rollback receipt, and
durably verify the result. It has no generic command, arbitrary path, plugin,
script, shell, remote execution, Production business-logic, SEC-02 decision,
or feature execution capability.

This is architecture only. It does not authorize implementation, installation,
activation, Production access, key creation, signing, notarization, or a
release. It does not claim that the future service is currently present.

## 2. Repository findings and non-reuse decision

Read-only inspection established the following repository facts:

- `scripts/build_governance_scheduler_smappservice.py` builds an independent
  scheduler application and applies ad hoc (`-`) code signatures. Its result
  explicitly records `production_registered: false`. It is not a Developer ID
  signed/notarized AIControlCenter release, installer, privileged helper, or
  anti-rollback authority.
- `deploy/macos/install-launchd.sh` copies a user LaunchAgent under the invoking
  user's home and bootstraps a `gui/${UID}` service. It has no authenticated
  release manifest, receipt, privileged installation boundary, or version
  monotonicity contract.
- the Mac Production Python Runtime architecture creates commit-specific
  immutable runtime directories and switches a `runtime/current` symlink only
  through explicit activation. Its prior target is rollback evidence, not
  rollback authority. It does not authenticate a signed/notarized application
  bundle or maintain the SEC-02 anti-rollback maxima.
- other repository rollback, deployment, DPL, Governance, and
  `ControlledExecutionPort` concepts do not supply a reusable generic
  authenticated release-install authority. DPL apply/install remains outside
  this boundary and must not be routed through generic remote commands.
- repository inspection did not prove a deployed signed/notarized
  `AIControlCenter.app`, a root-owned application installation, an
  authenticated release manifest, an installer package, an anti-rollback
  receipt, or a privileged installation helper.

Consequently, no existing subsystem is reclassified or extended into this
authority. Existing runtime activation remains separate and cannot advance the
receipt defined here.

## 3. Preserved authoritative facts

```text
SEC02_BOOTSTRAP_APPROVER_TRUST_SOURCE_ARCHITECTURE_FROZEN=YES
BOOTSTRAP_APPROVER_TRUST_SOURCE_OPERATIONALLY_DEFINED=NO
BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY

SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_ARCHITECTURE_FROZEN=YES
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_IMPLEMENTED=NO
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_OPERATIONALLY_VALIDATED=NO

SIGNED_APP_BUNDLE_CURRENTLY_DEPLOYED=NOT_ASSERTED
SIGNED_APP_BUNDLE_REQUIRED_FOR_FUTURE_BOOTSTRAP=YES

ROOT_WHEEL_INSTALL_STATE_CURRENTLY_PRESENT=NOT_ASSERTED
ROOT_WHEEL_INSTALL_POLICY=FUTURE_RELEASE_INSTALL_CONTRACT

ANTI_ROLLBACK_RECEIPT_REQUIRED=YES
ANTI_ROLLBACK_RECEIPT_AUTHORITY_DEFINED=NO
ANTI_ROLLBACK_RECEIPT_OPERATIONALLY_VALIDATED=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO

TRUST_OWNERSHIP_AUTHORITY=BOUND_DARWIN_PASSWD_RECORD
SEPARATE_UID_GID_AUTHORITY_REQUIRED=NO
```

The last two facts govern the generic SEC-02 trust directory and issuer
registry. Future `root:wheel` application-install ownership is a separate
installation policy. It does not replace, override, reinterpret, or become an
alternate source for the bound Darwin passwd ownership authority. Ownership,
UID, GID, and mode are defense-in-depth constraints, never cryptographic or
governance authenticity.

`ANTI_ROLLBACK_RECEIPT_AUTHORITY_DEFINED=NO` remains authoritative because this
freeze selects and bounds the architecture but does not establish concrete
signing identities, key custody, implementation, or operational proof.

## 4. Authority separation

The authority relation is:

```text
Release Authority
!= Human Bootstrap Approver
!= prospective SEC-02 Human Issuer
!= local runtime operator
!= bootstrap process
!= ordinary caller
!= SEC-02 intake
!= ControlledExecutionPort
!= WU09
!= Ubuntu
```

The existing invariant is preserved and extended:

```text
Issuer != Bootstrap Approver != Operator != Intake != Executor != Release Authority
```

The **Release Authority** is the independent human/organizational authority
that approves release source and controls the future Developer ID release and
installer signing identities. It authorizes a specific immutable release
transition by signing its canonical release manifest as part of a signed and
notarized installation package. Repository possession, a Git commit, an ad hoc
signature, notarization alone, operator consent, or administrator credentials
do not constitute Release Authority approval.

The **Mac Release Installation Authority** is a constrained local verifier and
state-transition mechanism. It may execute only a transition already
authorized by the Release Authority. It cannot manufacture release approval,
choose versions, amend a manifest, approve bootstrap, issue SEC-02 artifacts,
consume SEC-02 authorization, or invoke a feature executor.

The Human Bootstrap Approver signs only the one-time bootstrap approval. The
prospective issuer supplies only proposed public issuer facts. The operator may
initiate an explicitly authorized install but may not select or override any
security input. Bootstrap and SEC-02 intake are read-only consumers of the
verified installed state. `ControlledExecutionPort` and WU09 gain no install
or receipt capability. Ubuntu has zero authority and zero custody in this
architecture.

## 5. Authorized release input

The future installation authority accepts one immutable macOS installer
package through a fixed macOS installation interface. It accepts no loose app
bundle, caller-built manifest, alternate trust file, receipt, version override,
path override, URL, environment value, or generic command.

Acceptance requires all of the following as one fail-closed decision:

1. the package signature satisfies a future pinned AIControlCenter Installer
   Developer ID designated requirement and macOS trust evaluation;
2. the package is notarized and its notarization assessment succeeds;
3. its canonical, package-sealed release manifest is covered by that signature;
4. the manifest binds the package identity, monotonically ordered positive
   integer `release_version`, immutable `release_id`, exact application bundle
   digest and designated requirement, positive integer
   `bootstrap_trust_source_version`, exact trust-resource digest, receipt schema
   version, and transition nonce;
5. the application bundle satisfies the separately pinned AIControlCenter
   Application designated requirement, notarization policy, sealed-resource
   validation, manifest digest, and embedded trust-resource bindings; and
6. the release and installer signing roles and concrete designated requirements
   have been independently frozen, provisioned, and operationally validated.

The transition nonce is evidence correlation, not retry or replay authority.
The concrete Team ID, certificate requirements, release-manifest schema,
signing-key custody, revocation response, installer identity, installation
service identity, and key-recovery policy are unresolved operational inputs.
Their absence keeps implementation readiness blocked; no placeholder or
development identity may be accepted in Production.

## 6. Authenticated receipt authority and storage

The future Mac Release Installation Authority is the sole writer of the
anti-rollback receipt. The receipt is a canonical, bounded record containing at
least:

- receipt schema version and monotonically increasing receipt generation;
- highest authenticated accepted `release_version`;
- highest authenticated accepted `bootstrap_trust_source_version`;
- accepted release ID, release-manifest digest, app-bundle digest, and
  trust-resource digest;
- transition nonce and expected prior receipt generation and digest;
- installation phase and terminal-state classification;
- durable evidence references for package verification, bundle publication,
  receipt commitment, activation proof, and final verification; and
- a cryptographic authentication value over every receipt field.

The receipt requires cryptographic authentication, but this architecture does
not select its Production primitive. A future implementation freeze must
define and validate the exact primitive, algorithm, key custody, availability
behavior, creation ceremony, identity binding, export and backup policy, and
loss/recovery policy. No MAC, signature, P-256, Keychain, Secure Enclave,
software fallback, or other Production mechanism is authorized by this
correction. Failure to prove the selected design and its operational behavior
fails closed.

```text
RECEIPT_CRYPTOGRAPHIC_AUTHENTICATION_REQUIRED=YES
RECEIPT_CRYPTOGRAPHIC_PRIMITIVE_DEFINED=NO
SOFTWARE_CRYPTO_FALLBACK_AUTHORIZED=NO
SECURE_ENCLAVE_RECEIPT_PRIMITIVE_OPERATIONALLY_VALIDATED=NO
```

The authenticated receipt record itself must reside in a fixed Mac-local
system location outside the application bundle, use descriptor-relative
no-follow access, and be atomically replaced and durably synchronized by the
installation authority. Exact path and limits remain an implementation-freeze
decision. `root:wheel`, restrictive mode, ACL checks, link checks, filesystem
identity, and immutable-file handling are required defense in depth but do not
authenticate the receipt.

The receipt never:

- is caller supplied, bootstrap supplied, or operator selected;
- authenticates itself or derives authenticity solely from UID/GID/mode;
- grants bootstrap approval authority;
- grants SEC-02 authority; or
- grants execution authority.

## 7. First-install trust bootstrap

Receipt absence does not authenticate itself, and the candidate application
release does not authenticate the absence or create its own acceptance
authority. Local state absence does not prove first install. A non-circular,
persistent anchor that survives deletion of locally governed application state
is required to distinguish first install from reset, but that anchor is not
defined by this architecture.

```text
LOCAL_STATE_ABSENCE_PROVES_FIRST_INSTALL=NO
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
FIRST_INSTALL_REQUIRES_NON_CIRCULAR_PERSISTENT_ANCHOR=YES
APPLICATION_ACCESSIBLE_MONOTONIC_HARDWARE_COUNTER_CURRENTLY_PROVEN=NO
PERSISTENT_ANCHOR_ROLE=CONTINUITY_AND_ELIGIBILITY_EVIDENCE_ONLY
PERSISTENT_ANCHOR_MAY_GRANT_INSTALL_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_SEC02_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_EXECUTION_AUTHORITY=NO
FIRST_INSTALL_TRUST_BOOTSTRAP_GATE=BLOCKED_RESET_ANCHOR_UNDEFINED
```

Deleting the receipt, key, journal, evidence, and application must never make
an old valid release qualify automatically as generation 1. Absence of all
those objects is compatible with a reset attack and therefore cannot authorize
generation-1 creation. Any asserted first install remains blocked until the
installation authority can authenticate a non-circular persistent anchor and
prove that the anchor's state permits generation 1.

The package's signed manifest provides candidate values but cannot attest that
local prior state is absent or that absence means first install. The separately
installed, pinned installation authority may create generation 1 only after
the unresolved persistent anchor independently proves that the generation-1
eligibility and continuity precondition is satisfied. The actual release
transition remains authorized only by the separately frozen Release Authority
authorization and is performed only by the bounded Mac Release Installation
Authority.
Candidate application code and bootstrap code never establish the anchor or
create their own acceptance authority.

First-install acceptance remains blocked until the non-circular persistent
reset anchor, pinned installer identity, service establishment mechanism, and
receipt cryptographic primitive are concretely frozen and operationally
validated.

## 8. Update and stale-state semantics

Every update is a single explicitly authorized attempt with this state
transition:

```text
old authenticated state
-> authenticate authorized release transition
-> compare-and-swap against exact old generation and digest
-> publish exact verified inactive release
-> bounded receipt advancement
-> explicit activation step
-> durable end-to-end verification
```

Before any mutation, the installation authority obtains one descriptor-bound
snapshot of the authenticated receipt, installed release, active release, and
transition journal. The manifest must bind the observed prior receipt
generation and digest. Immediately before each mutation boundary the authority
must reauthenticate and compare the current generation, digest, installed
release identity, active state, and journal state with that snapshot.

Any mismatch, including a transition authorized from an outdated observation,
is `STALE_STATE` and fails closed before that mutation. It may not be refreshed
silently, rebased, adopted, merged, retried, or treated as the new old state.
A new observation and a new Release Authority authorization are required.

The candidate `release_version` must be strictly greater than the highest
authenticated release version:

```text
candidate.release_version > highest_authenticated_release_version
```

The candidate bootstrap trust-source version must be nondecreasing:

```text
candidate.bootstrap_trust_source_version
>= highest_authenticated_bootstrap_trust_source_version
```

If the trust-resource digest or content changes, its version must strictly
increase:

```text
candidate.bootstrap_trust_source_version
> highest_authenticated_bootstrap_trust_source_version
```

The same release version with a different artifact is prohibited. Any
candidate, installed bundle, active bundle, or embedded trust source below an
applicable authenticated maximum fails closed. A valid old signature does not
authorize downgrade. Receipt maxima never decrease, including during repair,
reconciliation, uninstall, key rotation, or application rollback.

```text
RELEASE_VERSION_STRICTLY_MONOTONIC=YES
TRUST_SOURCE_VERSION_NONDECREASING=YES
TRUST_SOURCE_CONTENT_CHANGE_REQUIRES_VERSION_INCREMENT=YES
SAME_RELEASE_VERSION_DIFFERENT_ARTIFACT_ALLOWED=NO
```

## 9. Atomicity and fail-closed ordering

macOS cannot be assumed to provide one atomic transaction spanning application
bundle publication, Keychain/Secure Enclave key use, receipt-file replacement,
activation, and durable evidence. This architecture does not claim such
atomicity.

Each individual filesystem publication and receipt replacement must be atomic
and durably synchronized, but the overall transition uses ordered, durably
journaled phases:

1. authenticate old state and package; write `PREPARED` evidence;
2. publish the fully verified candidate to a fixed inactive/versioned install
   location; verify it; write `RELEASE_PUBLISHED_RECEIPT_UNPROVEN`;
3. compare old state again; cryptographically commit the nondecreasing receipt;
   read it back and verify it; write `RECEIPT_ADVANCED_ACTIVATION_UNPROVEN`;
4. perform only the fixed application publication/activation operation; verify
   its exact code identity, version, digests, and receipt equality; and
5. write and re-read `FULLY_VERIFIED_INSTALLED` terminal evidence.

The former active release remains active through phase 2, but once a higher
receipt is committed, any lower active release is not SEC-02-bootstrap-eligible
and the system fails closed until explicit reconciliation proves activation of
the accepted release. No in-place bundle edit is permitted.

No phase marker authorizes its successor. Each phase requires the same explicit
transition authorization and exact compare-and-swap bindings during the one
invocation. After process exit, crash, timeout, lost acknowledgement, or an
unprovable durable write, that invocation has no continuing authority.

## 10. Crash, acknowledgement ambiguity, and reconciliation

An acknowledgement lost at any mutating boundary produces `AMBIGUOUS`, unless
a new read-only inspection can conclusively classify one of the more precise
terminal states below. Ambiguous receipt advancement is never silently replayed.
There is no automatic retry, rollback, compensation, completion, adoption, or
forward-fix authority.

Reconciliation is read-only by default. A later mutation requires a new,
separately issued Release Authority authorization that binds the exact observed
receipt generation/digest, journal state, installed/active release identities,
and one narrowly specified reconciliation transition. Administrator presence,
the original nonce, the original package, or the previous authorization does
not supply retry authority. Receipt maxima remain nondecreasing in every
reconciliation path.

Uninstall may remove activation only under a separately frozen uninstall
contract; it must not delete or reduce the receipt or its key. Receipt/key loss,
corruption, inaccessible hardware-backed key state, conflicting replicas, or
unprovable durability is fail-closed and has no recovery authority in this
freeze.

## 11. Durable terminal evidence

The installation journal and cryptographically authenticated receipt must be
sufficient for read-only inspection to distinguish exactly:

- `RELEASE_NOT_INSTALLED`: old authenticated receipt remains, no candidate was
  published, and durable evidence proves the attempt stopped before publication;
- `RELEASE_INSTALLED_RECEIPT_ADVANCEMENT_NOT_PROVEN`: the exact candidate is
  durably published inactive, but the new receipt cannot be authenticated and
  durably proven;
- `RECEIPT_ADVANCED_RELEASE_ACTIVATION_NOT_PROVEN`: the new receipt and inactive
  candidate are authenticated, but publication to the active application
  identity or its postcondition is not proven;
- `FULLY_VERIFIED_INSTALLED`: receipt, manifest, active bundle, code identity,
  release version, trust-source version, and all digests match, and terminal
  evidence was durably re-read; or
- `AMBIGUOUS`: facts conflict, a required acknowledgement or durable write is
  unproven, evidence is missing/corrupt, or no other classification is proven.

Only `FULLY_VERIFIED_INSTALLED` may be consumed by the future bootstrap
trust-source verifier, and even then it supplies authenticity/freshness facts
only. All other states deny bootstrap before authorization consumption. A
terminal record is evidence, not authority to retry, reconcile, bootstrap,
authorize SEC-02, activate, or execute.

## 12. Narrow privileged boundary

The installation authority's input language is closed and data-only: one
authenticated package reference obtained from the fixed macOS installation
session and its sealed manifest. Its output language is the bounded terminal
state and evidence schema above. It may access only fixed application staging,
publication, receipt, key, and journal objects.

It must not expose executable paths, command arrays, shell text, arbitrary file
operations, arbitrary service management, environment injection, working
directory selection, network retrieval, Docker access, SSH, Ubuntu transport,
`UbuntuWorkerClient.execute`, DPL apply, Governance calls, SEC-02 intake,
`ControlledExecutionPort`, WU09, secrets, commerce/CMS operations, Caddy, or
Production business logic. It is not a generic privileged executor or a second
governance engine.

Ubuntu is a stateless infrastructure worker with zero release approval,
installation, signature verification, receipt, key, state observation,
reconciliation, bootstrap, SEC-02, or execution authority. All authority and
durable state in this architecture remain on the Mac Control Plane.

## 13. Relationship to SEC-02

The future fully verified release receipt may allow the bootstrap verifier to
accept the release-bound Human Bootstrap Approver public resource as current.
It may never approve the bootstrap ceremony or grant bootstrap authority. The
existing signed Human Bootstrap Approver approval, separation checks, bounded
one-time bootstrap protocol, consumption semantics, registry postcondition,
and sealing requirements remain unchanged.

The generic SEC-02 trust directory remains governed by
`TRUST_OWNERSHIP_AUTHORITY=BOUND_DARWIN_PASSWD_RECORD` and
`SEPARATE_UID_GID_AUTHORITY_REQUIRED=NO`. The release installer may install the
application under the future `root:wheel` contract; it may not create, repair,
own, rewrite, or authorize the generic SEC-02 trust directory or registry.

Governance core, `ControlledExecutionPort`, WU09, and SEC-02 semantics are not
changed by this freeze.

## 14. Readiness and unresolved blockers

This architecture resolves the conceptual authority separation, monotonic
update rule, stale-state behavior, non-atomic ordering, ambiguity handling,
and terminal evidence model. First-install/reset trust remains unresolved. It
does not provide the concrete and operationally proven dependencies required
for implementation.

The following remain blockers:

- independently approved Release Authority governance and key custody;
- pinned Installer and Application Developer ID designated requirements;
- authenticated release-manifest schema and signing/notarization pipeline;
- exact macOS installation-service establishment and update mechanism;
- non-circular persistent first-install/reset anchor that cannot be reset by
  deleting application-accessible receipt, key, journal, evidence, and bundle;
- exact receipt cryptographic primitive, access-control identity,
  receipt path/schema/limits, key-loss policy, and journal durability design;
- exact inactive publication and active application paths and activation API;
- signed/notarized installer and application artifacts plus negative-path,
  crash-point, stale-state, downgrade, and durability validation.

Therefore this freeze does **not** make
`SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION` ready. The status remains
`NOT_READY`. The bootstrap trust source remains operationally undefined,
implementation authority is not ready, and Production bootstrap is unavailable.

## 15. Final review gates

```text
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_PRECISION_GATE=PASS
FIRST_INSTALL_TRUST_BOOTSTRAP_GATE=BLOCKED_RESET_ANCHOR_UNDEFINED
FIRST_INSTALL_RESET_ATTACK_GATE=BLOCKED
LOCAL_ABSENCE_AUTHORITY_GATE=PASS_NONE_GRANTED
NON_CIRCULAR_PERSISTENT_ANCHOR_GATE=BLOCKED_UNDEFINED
RECEIPT_CRYPTO_PRIMITIVE_GATE=BLOCKED_UNDEFINED
SOFTWARE_CRYPTO_FALLBACK_GATE=PASS_NONE_AUTHORIZED
RELEASE_VERSION_MONOTONICITY_GATE=PASS_STRICT
TRUST_SOURCE_VERSION_MONOTONICITY_GATE=PASS_NONDECREASING_CONTENT_CHANGE_STRICT
SAME_VERSION_DIFFERENT_ARTIFACT_GATE=PASS_PROHIBITED
RELEASE_AUTHORITY_SEPARATION_GATE=PASS
PERSISTENT_ANCHOR_AUTHORITY_SEPARATION_GATE=PASS
ANTI_ROLLBACK_NO_BOOTSTRAP_AUTHORITY_GATE=PASS
ANTI_ROLLBACK_NO_SEC02_AUTHORITY_GATE=PASS
ANTI_ROLLBACK_NO_EXECUTION_AUTHORITY_GATE=PASS
STALE_STATE_FAIL_CLOSED_GATE=PASS
DOWNGRADE_FAIL_CLOSED_GATE=PASS
AMBIGUOUS_UPDATE_FAIL_CLOSED_GATE=PASS
AUTOMATIC_RETRY_AUTHORITY_GATE=PASS_NONE_GRANTED
ATOMICITY_MODEL_GATE=PASS_NON_ATOMIC_FAIL_CLOSED
MAC_CONTROL_PLANE_GATE=PASS
UBUNTU_ZERO_AUTHORITY_GATE=PASS
GENERIC_EXECUTOR_GATE=PASS_NONE_CREATED
TRUST_OWNERSHIP_INVARIANT_PRESERVED_GATE=PASS
SIGNED_RELEASE_CURRENT_STATE_ASSUMPTION_GATE=PASS_NOT_ASSERTED
INSTALL_POLICY_CURRENT_STATE_ASSUMPTION_GATE=PASS_NOT_ASSERTED

SEC02_BOOTSTRAP_APPROVER_TRUST_SOURCE_ARCHITECTURE_FROZEN=YES
BOOTSTRAP_APPROVER_TRUST_SOURCE_OPERATIONALLY_DEFINED=NO
BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO

SIGNED_APP_BUNDLE_CURRENTLY_DEPLOYED=NOT_ASSERTED
SIGNED_APP_BUNDLE_REQUIRED_FOR_FUTURE_BOOTSTRAP=YES

ROOT_WHEEL_INSTALL_STATE_CURRENTLY_PRESENT=NOT_ASSERTED
ROOT_WHEEL_INSTALL_POLICY=FUTURE_RELEASE_INSTALL_CONTRACT

ANTI_ROLLBACK_RECEIPT_REQUIRED=YES
ANTI_ROLLBACK_RECEIPT_AUTHORITY_DEFINED=NO
ANTI_ROLLBACK_RECEIPT_OPERATIONALLY_VALIDATED=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO

RECEIPT_CRYPTOGRAPHIC_AUTHENTICATION_REQUIRED=YES
RECEIPT_CRYPTOGRAPHIC_PRIMITIVE_DEFINED=NO
SOFTWARE_CRYPTO_FALLBACK_AUTHORIZED=NO
SECURE_ENCLAVE_RECEIPT_PRIMITIVE_OPERATIONALLY_VALIDATED=NO

LOCAL_STATE_ABSENCE_PROVES_FIRST_INSTALL=NO
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
FIRST_INSTALL_REQUIRES_NON_CIRCULAR_PERSISTENT_ANCHOR=YES
APPLICATION_ACCESSIBLE_MONOTONIC_HARDWARE_COUNTER_CURRENTLY_PROVEN=NO

RELEASE_VERSION_STRICTLY_MONOTONIC=YES
TRUST_SOURCE_VERSION_NONDECREASING=YES
TRUST_SOURCE_CONTENT_CHANGE_REQUIRES_VERSION_INCREMENT=YES
SAME_RELEASE_VERSION_DIFFERENT_ARTIFACT_ALLOWED=NO

TRUST_OWNERSHIP_AUTHORITY=BOUND_DARWIN_PASSWD_RECORD
SEPARATE_UID_GID_AUTHORITY_REQUIRED=NO

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

`SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_PRECISION_GATE=PASS` means the
permissible future authority and its limits are precisely frozen. It does not contradict
`ANTI_ROLLBACK_RECEIPT_AUTHORITY_DEFINED=NO`: no concrete operational identity,
cryptographic mechanism, installed writer, or validated receipt currently
exists. Architecture frozen, implementation complete, and operationally
validated are separate states and must never be inferred from one another.
