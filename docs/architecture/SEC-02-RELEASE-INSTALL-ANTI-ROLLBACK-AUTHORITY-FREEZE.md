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
SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY
PRODUCTION_BOOTSTRAP_AVAILABLE=NO

MAC_MINI_M4_CONTROL_PLANE=SOLE
CONTINUITY_WITNESS_AUTHORITY=EXTERNAL_DURABLE_EVIDENCE_ONLY
CONTINUITY_WITNESS_SECOND_CONTROL_PLANE=NO
UBUNTU_ROLE=STATELESS_INFRASTRUCTURE_WORKER_ONLY
UBUNTU_AUTHORITY=ZERO

SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_ARCHITECTURE_FROZEN=YES
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_IMPLEMENTED=NO
SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_OPERATIONALLY_VALIDATED=NO

SIGNED_APP_BUNDLE_CURRENTLY_DEPLOYED=NOT_ASSERTED
SIGNED_APP_BUNDLE_REQUIRED_FOR_FUTURE_BOOTSTRAP=YES

ROOT_WHEEL_INSTALL_STATE_CURRENTLY_PRESENT=NOT_ASSERTED
ROOT_WHEEL_INSTALL_POLICY=FUTURE_RELEASE_INSTALL_CONTRACT

ANTI_ROLLBACK_RECEIPT_REQUIRED=YES
ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_DEFINED=YES
ANTI_ROLLBACK_RECEIPT_IMPLEMENTED=NO
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

`ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_DEFINED=YES` means the repository contract
is complete enough for a later implementation work unit. It does not establish
an installed writer, create a key, validate Secure Enclave behavior, or make
Production bootstrap available.

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

The selected receipt authentication primitive is ECDSA over NIST P-256 with
SHA-256, using a non-exportable Secure Enclave private key. The signed message
is the RFC 8785 JCS encoding of the receipt payload. The stored signature is
strict unpadded base64url of the fixed-width 64-byte `r || s` representation;
`r` and `s` are unsigned, big-endian, 32-byte values and `s` must be in the
lower half of the P-256 group order. Verification rejects non-canonical JCS,
DER signatures, padded base64, non-low-S signatures, alternate encodings, or a
signature made over any other bytes. The receipt key ID is strict unpadded
base64url SHA-256 of the 65-byte ANSI X9.63 uncompressed public key.

The private key is created and used only by the future purpose-built Mac
Release Installation Authority under a dedicated Keychain access group and a
pinned production code-signing designated requirement. Its private material is
non-exportable, has `privateKeyUsage` access only, is not synchronizable, is
not backed up, and is unavailable to the application, bootstrap, operator,
Ubuntu, Witness, Governance, SEC-02, and feature executors. Root identity,
Keychain ACLs, entitlements, and code identity are jointly required access
controls; none alone is receipt authenticity or release authorization.
Key creation is permitted only during a separately authorized GENESIS or
RECOVERY ceremony after exact Witness evidence. Normal install/update may
never create, replace, import, select, or fall back from the key.

```text
RECEIPT_CRYPTOGRAPHIC_AUTHENTICATION_REQUIRED=YES
RECEIPT_CRYPTOGRAPHIC_PRIMITIVE_DEFINED=YES
RECEIPT_SIGNING_PRIMITIVE=ECDSA_P256_SHA256
RECEIPT_SIGNING_KEY_CUSTODY=MAC_SECURE_ENCLAVE_NON_EXPORTABLE
RECEIPT_SIGNING_KEY_ACCESS_IDENTITY=PINNED_MAC_RELEASE_INSTALLATION_AUTHORITY
SOFTWARE_CRYPTO_FALLBACK_AUTHORIZED=NO
SECURE_ENCLAVE_RECEIPT_PRIMITIVE_OPERATIONALLY_VALIDATED=NO
```

The fixed storage root is
`/Library/Application Support/AIControlCenter/Security/AntiRollback`. It is on
the same local APFS volume as all of its children and contains only
`receipt.v1.json`, `journal/`, and installation-authority-owned temporary files
during one invocation. The root and `journal/` are real directories owned by
`root:wheel`, mode `0700`, not symlinks, with no ACL, flags, or extended
attributes that grant another writer. Receipt, journal, and temporary objects
are regular files owned by `root:wheel`, mode `0600`, link count one, never
symlinks, hard links, sockets, devices, FIFOs, aliases, clones accepted from a
caller, or sparse files. The receipt is at most 16,384 bytes; each journal
record is at most 32,768 bytes; the journal has at most one record per receipt
generation plus one unresolved attempt and is otherwise a closed failure.

Every path component is opened from a pinned root descriptor with no-follow
semantics. Validation and I/O remain bound to the same descriptor, device, and
inode; path re-resolution after validation is forbidden. The installation
authority rejects unexpected entries, mounts, owners, modes, ACLs, flags,
links, sizes, file types, descriptor changes, or filesystem ambiguity.
Filesystem metadata is defense in depth and never replaces signature or
Witness verification.

The receipt never:

- is caller supplied, bootstrap supplied, or operator selected;
- authenticates itself or derives authenticity solely from UID/GID/mode;
- grants bootstrap approval authority;
- grants SEC-02 authority; or
- grants Production mutation, `ControlledExecutionPort`, execution, retry, or
  rollback authority.

### 6.1 Canonical schema, identity, and version model

`receipt.v1.json` is one UTF-8 JSON object with no BOM, duplicate keys,
floats, exponent notation, implicit nulls, unknown fields, or trailing bytes.
It must equal its RFC 8785 JCS serialization byte for byte. All digests and the
signature use strict unpadded base64url. SHA-256 digests are exactly 32 bytes;
UUIDs are lowercase canonical UUIDv7 strings; integers are positive JSON safe
integers no greater than 9,007,199,254,740,991; timestamps are UTC RFC 3339
with exactly microsecond precision and `Z` and never decide monotonicity.

The closed schema is:

```json
{
  "schema_version": "1",
  "domain": "AICONTROLCENTER_ANTI_ROLLBACK_RECEIPT",
  "receipt_id": "<UUIDv7 assigned once by the installation authority>",
  "continuity_host_id": "<Witness-assigned UUIDv7>",
  "receipt_generation": 1,
  "previous_receipt_digest": null,
  "release_version": 1,
  "bootstrap_trust_source_version": 1,
  "release_id": "<nonempty immutable release identifier>",
  "release_manifest_digest": "<base64url SHA-256>",
  "app_bundle_digest": "<base64url SHA-256>",
  "trust_resource_digest": "<base64url SHA-256>",
  "transition_nonce": "<base64url 32 bytes from the sealed manifest>",
  "witness_record_generation": 1,
  "witness_transition_digest": "<base64url SHA-256>",
  "witness_checkpoint_id": "<Witness-assigned UUIDv7>",
  "witness_checkpoint_object_digest": "<base64url SHA-256>",
  "receipt_key_id": "<base64url SHA-256 of X9.63 public key>",
  "committed_at": "<UTC RFC3339 microseconds>",
  "state": "COMMITTED",
  "signature": "<base64url 64-byte canonical P-256 signature>"
}
```

The signature covers the complete object excluding only `signature`. For
generation 1, `previous_receipt_digest` is JSON null; for every later
generation it is the SHA-256 of the complete prior canonical receipt including
its signature. Receipt identity is the tuple
`(continuity_host_id, receipt_generation, receipt_id)`. Generation is exactly
one greater than the authenticated prior generation and never resets for the
same continuity host. A repeated receipt ID or generation with different
canonical bytes is conflict, not an alternate replica. No field is optional.

### 6.2 Witness binding and authoritative durability

The local receipt is the authoritative Mac-local installed-version state. The
already frozen external Continuity Witness is the non-circular persistent
continuity anchor. No new persistent-authority subsystem is created. For every
release transition, its existing PostgreSQL record and S3 Object Lock
Compliance checkpoint history must durably record the same host, new record
generation, release/trust-source maxima, release ID, manifest/app/trust
digests, prior and resulting transition digests, and local receipt public-key
ID before the local receipt can be committed. The checkpoint's opaque S3
VersionId and object digest are bound into the local receipt. Retention covers
the full Continuity Authority lifetime.

The Witness operation is a purpose-bound evidence append authenticated as
coming from the pinned Mac Release Installation Authority and bound to one
Release Authority-authorized manifest and the exact prior Witness state. It
records evidence only: it does not approve the release, choose values, grant
install authority, advance the Mac-local receipt, or become a Control Plane.
The later Witness repository implementation must add this closed release-
observation operation; it must not expose generic mutation or command input.

Before install, the Mac authority performs fresh challenge-bound read-only
continuity verification. `CONTINUITY_VALID` must bind the exact host, current
Witness generation/digest, maxima, and receipt key ID. Missing local state is
handled only as `RECOVERY_REQUIRED` or an independently approved
`GENESIS_ELIGIBLE`; the caller cannot select either. After Witness evidence is
durably checkpointed and exactly re-read, the Mac authority may commit the
matching local receipt. Thus a crash after Witness advancement but before the
local commit leaves a safe, closed stale-local condition. Local-first commit is
forbidden because deletion before Witness durability could erase the higher
floor.

```text
WITNESS_DURABILITY_PRECEDES_LOCAL_RECEIPT_COMMIT=YES
POSTGRESQL_ALONE_PROVES_WITNESS_DURABILITY=NO
S3_CURRENT_KEY_VIEW_PROVES_HISTORY=NO
WITNESS_RECORDS_EVIDENCE_NOT_AUTHORITY=YES
MAC_RELEASE_INSTALLATION_AUTHORITY_SOLE_LOCAL_RECEIPT_WRITER=YES
```

### 6.3 Durable atomic update and journal

There is no claimed cross-system transaction. One invocation uses the exact
ordering below and a signed, durably retained phase journal record keyed by
`<receipt_generation>-<receipt_id>.v1.json`:

1. descriptor-bind and authenticate the local receipt/key/journal; obtain and
   verify fresh Witness evidence; validate the exact release authorization;
2. create the journal record in `PREPARED`, binding the complete old state,
   proposed receipt digest, package facts, Witness request/operation IDs, and
   phase; write with exclusive create, fully synchronize the file and journal
   directory, then re-read and verify it;
3. publish and verify the inactive release; atomically replace the same journal
   record with `RELEASE_PUBLISHED_WITNESS_UNPROVEN` using a same-directory
   exclusive temporary regular file, file full-sync, atomic `renameat`, parent
   directory full-sync, and descriptor-bound re-read;
4. submit the single evidence append to the Witness without automatic retry;
   reconcile ambiguity only through read-only exact-ID queries; after exact
   PostgreSQL/checkpoint proof, record `WITNESS_COMMITTED_LOCAL_UNPROVEN` with
   the same atomic/full-sync protocol;
5. sign the canonical receipt, atomically replace `receipt.v1.json` with a
   same-directory exclusive temporary file, full-sync file, atomic `renameat`,
   full-sync storage-root directory, then reopen, reauthenticate, and compare
   exact bytes, generation, digest, and Witness bindings;
6. perform the separately bounded activation, verify the active release, and
   atomically/full-sync the journal terminal state `FULLY_VERIFIED_INSTALLED`.

“Full-sync” means the strongest implementation-proven macOS durable-file and
directory synchronization sequence, including `F_FULLFSYNC` where supported;
unsupported or uncertain durability is failure. Temporary names contain only
the authority-generated receipt ID, are never caller-selected, and stale
temporaries are ambiguous evidence. Journal records are signed with the same
receipt key and domain `AICONTROLCENTER_ANTI_ROLLBACK_JOURNAL`; each binds the
prior journal digest. They are retained, not truncated or rewritten as history.
Only the current attempt's phase file is atomically replaced.

No journal phase, nonce, old authorization, or exact stored response grants
completion, retry, rollback, or reconciliation mutation authority. Crash,
timeout, lost acknowledgement, partial publication, extra/missing record,
chain break, or uncertain synchronization stops. A new invocation is read-only
reconciliation unless a new Release Authority authorization explicitly binds
the exact observed local, Witness, journal, installed, and active state.

### 6.4 Read-only reconciliation and closed failures

Reconciliation opens one descriptor-bound snapshot and verifies, without
mutation: receipt canonical form and signature; public-key identity and access
status; journal chain and terminal phase; installed and active artifact facts;
fresh signed Witness evidence; PostgreSQL/checkpoint agreement; and equality of
host, generations, maxima, IDs, digests, and key binding. It returns only the
five classifications in section 11. It never repairs, adopts, completes,
retries, rolls back, selects a replica, recreates a key, or restores authority.

Missing, malformed, noncanonical, oversized, hard-linked, symlinked,
conflicting, duplicated, stale, downgraded, unverifiable, key-mismatched, or
ambiguous local/Witness evidence denies installation and bootstrap. A missing,
lost, disabled, inaccessible, duplicated, or ambiguity-status receipt key also
denies. Key recovery requires a separately frozen Human Continuity Lifecycle
RECOVERY ceremony, fresh hardware evidence, complete immutable-history proof,
and a new exact Release Authority authorization; this architecture defines no
automatic key recovery or software fallback. Key compromise/revocation remains
a later operational ceremony and cannot reduce maxima.

## 7. First-install trust bootstrap

Receipt absence does not authenticate itself, and the candidate application
release does not authenticate the absence or create its own acceptance
authority. Local state absence does not prove first install. A non-circular,
persistent anchor that survives deletion of locally governed application state
is required to distinguish first install from reset. The already frozen
external Continuity Witness supplies that anchor; this receipt creates no
second anchor.

```text
LOCAL_STATE_ABSENCE_PROVES_FIRST_INSTALL=NO
FIRST_INSTALL_RESET_ATTACK_RESOLVED=NO
FIRST_INSTALL_RESET_ATTACK_ARCHITECTURE_RESOLVED=YES
FIRST_INSTALL_REQUIRES_NON_CIRCULAR_PERSISTENT_ANCHOR=YES
APPLICATION_ACCESSIBLE_MONOTONIC_HARDWARE_COUNTER_CURRENTLY_PROVEN=NO
PERSISTENT_ANCHOR_ROLE=CONTINUITY_AND_ELIGIBILITY_EVIDENCE_ONLY
PERSISTENT_ANCHOR_MAY_GRANT_INSTALL_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_SEC02_AUTHORITY=NO
PERSISTENT_ANCHOR_MAY_GRANT_EXECUTION_AUTHORITY=NO
FIRST_INSTALL_TRUST_BOOTSTRAP_GATE=PASS_ARCHITECTURE_DEFINED_NOT_IMPLEMENTED
```

Deleting the receipt, key, journal, evidence, and application must never make
an old valid release qualify automatically as generation 1. Absence of all
those objects is compatible with a reset attack and therefore cannot authorize
generation-1 creation. Any asserted first install remains blocked unless the
installation authority authenticates the already selected external Continuity
Witness and receives fresh `GENESIS_ELIGIBLE` evidence backed by complete
PostgreSQL and S3 Object Lock Compliance history coverage.

The package's signed manifest provides candidate values but cannot attest that
local prior state is absent or that absence means first install. The separately
installed, pinned installation authority may create generation 1 only after
the Continuity Witness independently proves that the generation-1
eligibility and continuity precondition is satisfied. The actual release
transition remains authorized only by the separately frozen Release Authority
authorization and is performed only by the bounded Mac Release Installation
Authority.
Candidate application code and bootstrap code never establish the anchor or
create their own acceptance authority.

The first-install/reset architecture is defined, but acceptance remains
operationally blocked until the Witness, pinned installer identity, service,
receipt primitive, and GENESIS ceremony are implemented and validated.

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
atomicity. Section 6.3 is the authoritative detailed ordering and journal
contract; the following is its higher-level phase summary.

Each individual filesystem publication and receipt replacement must be atomic
and durably synchronized, but the overall transition uses ordered, durably
journaled phases:

1. authenticate old state and package; write `PREPARED` evidence;
2. publish the fully verified candidate to a fixed inactive/versioned install
   location; verify it; write `RELEASE_PUBLISHED_WITNESS_UNPROVEN`;
3. compare old state again; append and exactly prove the matching Witness
   PostgreSQL and immutable checkpoint evidence; write
   `WITNESS_COMMITTED_LOCAL_UNPROVEN`;
4. cryptographically commit, read back, and verify the nondecreasing local
   receipt; write `RECEIPT_ADVANCED_ACTIVATION_UNPROVEN`;
5. perform only the fixed application publication/activation operation; verify
   its exact code identity, version, digests, and receipt equality; and
6. write and re-read `FULLY_VERIFIED_INSTALLED` terminal evidence.

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
unprovable durability is fail-closed. Recovery is not automatic and remains an
unimplemented separately governed ceremony under section 6.4.

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

This architecture resolves the receipt schema, identity, cryptographic
primitive, key custody, storage, journal durability, authority separation,
monotonic update rule, stale-state behavior, non-atomic ordering, ambiguity
handling, Witness binding, and terminal evidence model. The existing
Continuity Witness resolves first-install/reset at architecture level. None is
implemented or operationally validated.

The following remain blockers:

- independently approved Release Authority governance and key custody;
- pinned Installer and Application Developer ID designated requirements;
- authenticated release-manifest schema and signing/notarization pipeline;
- exact macOS installation-service establishment and update mechanism;
- repository implementation of the purpose-bound Witness release-observation
  operation and its exact API/schema/transaction tests;
- Secure Enclave/Keychain entitlement, code-requirement, signature encoding,
  filesystem full-sync, atomic replacement, and crash-point validation on the
  target macOS and hardware;
- GENESIS key creation and RECOVERY/key-loss ceremonies consistent with the
  frozen Witness lifecycle and complete immutable-history proof;
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
SEC02_AR_01_GATE=PASS
ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_GATE=PASS_DEFINED_NOT_IMPLEMENTED
FIRST_INSTALL_TRUST_BOOTSTRAP_GATE=PASS_ARCHITECTURE_DEFINED_NOT_IMPLEMENTED
FIRST_INSTALL_RESET_ATTACK_GATE=PASS_ARCHITECTURE_ONLY
LOCAL_ABSENCE_AUTHORITY_GATE=PASS_NONE_GRANTED
NON_CIRCULAR_PERSISTENT_ANCHOR_GATE=PASS_EXISTING_CONTINUITY_WITNESS
RECEIPT_CRYPTO_PRIMITIVE_GATE=PASS_P256_SECURE_ENCLAVE_DEFINED_NOT_VALIDATED
RECEIPT_KEY_CUSTODY_GATE=PASS_DEFINED_NOT_IMPLEMENTED
RECEIPT_DURABLE_STORAGE_GATE=PASS_DEFINED_NOT_IMPLEMENTED
RECEIPT_JOURNAL_DURABILITY_GATE=PASS_DEFINED_NOT_IMPLEMENTED
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
SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION=NOT_READY
PRODUCTION_BOOTSTRAP_AVAILABLE=NO

SIGNED_APP_BUNDLE_CURRENTLY_DEPLOYED=NOT_ASSERTED
SIGNED_APP_BUNDLE_REQUIRED_FOR_FUTURE_BOOTSTRAP=YES

ROOT_WHEEL_INSTALL_STATE_CURRENTLY_PRESENT=NOT_ASSERTED
ROOT_WHEEL_INSTALL_POLICY=FUTURE_RELEASE_INSTALL_CONTRACT

ANTI_ROLLBACK_RECEIPT_REQUIRED=YES
ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_DEFINED=YES
ANTI_ROLLBACK_RECEIPT_IMPLEMENTED=NO
ANTI_ROLLBACK_RECEIPT_OPERATIONALLY_VALIDATED=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_BOOTSTRAP_AUTHORITY=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_SEC02_AUTHORITY=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_EXECUTION_AUTHORITY=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_RETRY_AUTHORITY=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_ROLLBACK_AUTHORITY=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_PRODUCTION_MUTATION_AUTHORITY=NO
ANTI_ROLLBACK_RECEIPT_MAY_GRANT_CONTROLLED_EXECUTION_PORT_AUTHORITY=NO

RECEIPT_CRYPTOGRAPHIC_AUTHENTICATION_REQUIRED=YES
RECEIPT_CRYPTOGRAPHIC_PRIMITIVE_DEFINED=YES
RECEIPT_KEY_CUSTODY_ARCHITECTURE_DEFINED=YES
RECEIPT_DURABLE_STORAGE_ARCHITECTURE_DEFINED=YES
RECEIPT_JOURNAL_DURABILITY_ARCHITECTURE_DEFINED=YES
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

`SEC02_RELEASE_INSTALL_ANTI_ROLLBACK_AUTHORITY_PRECISION_GATE=PASS` and
`ANTI_ROLLBACK_RECEIPT_ARCHITECTURE_DEFINED=YES` mean the permissible future
authority, data, primitive, custody, and durability contracts are precisely
frozen. No installed writer, created key, receipt, cloud resource, or validated
mechanism currently exists. Architecture frozen, implementation complete, and
operationally validated are separate states and must never be inferred from
one another.
