# SEC-02 Bootstrap Approver Trust Source Architecture Freeze

Status: **FROZEN**

```text
SEC02_BOOTSTRAP_APPROVER_TRUST_SOURCE_FREEZE=COMPLETE
SEC02_BOOTSTRAP_APPROVER_TRUST_SOURCE_ARCHITECTURE_FROZEN=YES
BOOTSTRAP_APPROVER_TRUST_SOURCE_OPERATIONALLY_DEFINED=NO
BOOTSTRAP_IMPLEMENTATION_AUTHORITY_READY=NO
PRODUCTION_BOOTSTRAP_AVAILABLE=NO
```

## 1. Decision and scope

The Human Bootstrap Approver trust source is a **minimal, release-bound Mac
application resource** containing only the public Ed25519 verification facts
needed to authenticate the bootstrap approval defined by the already frozen
SEC-02 Production Trust Bootstrap protocol.

It is not the generic SEC-02 human-issuer trust registry. It is not supplied by
the bootstrap record and is not writable by bootstrap. It grants only the
ability to answer a read-only question: whether one bootstrap approval signature
is valid under an independently released Human Bootstrap Approver public key.
Successful verification grants zero execution authority, zero SEC-02
authorization authority, zero WU09 authority, and zero registry-mutation
authority. The separate frozen bootstrap lifecycle and all of its preconditions
remain mandatory.

This is an architecture-only decision. It creates no implementation authority,
Production trust material, signing key, bootstrap availability, or operational
authorization.

## 2. Preserved authoritative facts

```text
TRUST_OWNERSHIP_AUTHORITY=BOUND_DARWIN_PASSWD_RECORD
SEPARATE_UID_GID_AUTHORITY_REQUIRED=NO
CALLER_UID_GID_AUTHORITY_ALLOWED=NO

BOOTSTRAP_APPROVAL_PROTOCOL_DEFINED=YES
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

TRUST_DIRECTORY_MUST_PREEXIST=YES
BOOTSTRAP_MAY_CREATE_TRUST_DIRECTORY=NO
BOOTSTRAP_MAY_REPAIR_TRUST_DIRECTORY=NO
```

`TRUST_OWNERSHIP_AUTHORITY` continues to govern the generic SEC-02 trust
directory and issuer registry. This freeze introduces no alternate UID/GID
input and does not change that registry's bound-Darwin-passwd ownership policy.
The release resource is governed by the separate application-install boundary,
not by caller-selected ownership.

## 3. Selected mechanism

The selected mechanism is the smallest form of option 1: repository/release-
bound immutable public material embedded as a resource in the signed and
notarized Mac AIControlCenter application bundle. It is not a general keyring.
The signed and notarized application bundle is the frozen **required future
Production release form** for this trust-source architecture unless separately
proven by operational validation. This freeze does not assert that such a
bundle is the current Production deployment fact.
Its logical release-relative path is exactly:

```text
AIControlCenter.app/Contents/Resources/governance/bootstrap/sec02-bootstrap-approvers.v1.json
```

Runtime discovers the containing application bundle from its authenticated
executable identity. An absolute path, bundle path, resource path, key, key ID,
version, or platform supplied through API input, bootstrap record, environment,
`HOME`, argv, current working directory, operator choice, or caller choice is
prohibited.

The resource contains only:

- schema version;
- trust-source version;
- release identifier;
- exactly one active Human Bootstrap Approver identity;
- exactly one key identifier;
- algorithm, exactly `Ed25519`;
- exactly one 32-byte public verification key in canonical unpadded base64url;
- `not_before` and `not_after` validity bounds; and
- a deterministic resource digest.

Multiple active approvers, alternate keys, fallback keys, key discovery,
algorithm negotiation, network retrieval, and caller selection are prohibited.
The corresponding private key is never a field, input, resource, secret,
fallback, or Production asset.

## 4. Source of truth and authority separation

The reviewed release source is the source of truth for the public resource.
The independent AIControlCenter release authority owns approval of changes to
that source and production of the signed/notarized Mac release. The Human
Bootstrap Approver owns the offline private signing key. These authorities must
be distinct from the prospective issuer, local bootstrap operator, intake
identity, executor identity, WU09, Ubuntu, and ordinary callers.

The authority boundaries remain:

```text
Issuer != Approver != Operator != Intake != Executor
```

Repository possession, a working-tree edit, or an unsigned development build
does not establish Production trust. The bootstrap operator cannot select,
install, edit, replace, or bless approver material as part of the bootstrap
ceremony. The prospective issuer cannot sign the release trust source or add
itself. The approval being verified cannot authenticate its own verifier.

## 5. Installation and provisioning boundary

Future provisioning may occur only as part of a separately authorized Mac
application release installation. The required future signed/notarized
application bundle and its authenticated release manifest must carry the
resource. No current Production bundle, resource, ownership, mode, or installer
state is asserted by this freeze. Bootstrap, SEC-02 intake, Governance,
`ControlledExecutionPort`, WU09, Docker, Ubuntu, an API caller, and an ordinary
operator perform no trust-source installation or repair.

As a future release-installer contract, the bundle root and governed resource
ancestors must be real, non-symlink directories owned exactly by `root:wheel`
with exact mode `0755`. The resource must be a regular, non-symlink file owned
exactly by `root:wheel` with exact mode `0444`. ACLs granting mutation, extended
attributes that redirect or substitute content, group/other write bits, and
hard-link ambiguity are prohibited. The application install/update mechanism
must publish the whole verified bundle atomically; in-place resource edits are
prohibited.

These install ownership facts do not replace the bound Darwin passwd record as
authority for the generic SEC-02 trust directory. No second runtime UID/GID
authority is accepted from a caller.

## 6. Integrity and authenticity binding

Runtime trust requires all of the following as one fail-closed decision:

1. Darwin on the Mac Control Plane;
2. the running executable and containing bundle satisfy the pinned
   AIControlCenter designated code-signing requirement;
3. the bundle's notarized release identity is valid under macOS trust
   evaluation;
4. the resource is covered by that exact bundle's sealed-resource manifest;
5. the authenticated release identifier equals the resource release identifier;
6. descriptor-relative, no-follow traversal from the authenticated bundle is
   used, with no pathname re-resolution after validation;
7. ownership, modes, type, link count, bounded size, canonical encoding,
   schema, digest, version, key uniqueness, identity, algorithm, and validity
   all pass; and
8. validation and reading remain bound to the same file descriptor, inode, and
   device identity.

A detached signature or digest shipped beside the resource is insufficient by
itself. Authenticity comes from the independently authorized signed release;
the internal digest detects canonical-content mismatch but does not bootstrap
trust. Development, ad hoc-signed, unsigned, unnotarized, or signature-invalid
bundles are never acceptable for Production bootstrap verification.

## 7. Versioning, freshness, and rotation

`schema_version` is exactly `1`. `trust_source_version` is a positive,
monotonically increasing integer. The release identifier, trust-source version,
approver identity, key ID, public key, and validity interval are all sealed into
the authenticated release resource. `not_before` and `not_after` are mandatory;
non-expiring keys are prohibited.

Rotation or revocation requires a new independently reviewed, signed, notarized,
and separately authorized application release with a higher trust-source
version. Bootstrap cannot update the resource. There is no local enrollment,
hot reload, overlay, automatic fetch, network discovery, alternate file, or
fallback to an earlier version.

The future installer must maintain an independently authenticated Mac-local
anti-rollback installation receipt recording the highest accepted release and
trust-source versions. The receipt is required, but this freeze does not define
the concrete authenticated storage mechanism, authenticated update mechanism,
or authority capable of advancing it. Those are a separate release-install and
anti-rollback authority boundary. The receipt belongs to that boundary, not to
bootstrap, and must not be writable or selectable by the runtime operator.

The receipt must never be caller supplied, bootstrap supplied, operator-
selected, or self-authenticating. Its authenticity must not derive solely from
UID, GID, ownership, or mode. It grants no bootstrap approval authority, no
SEC-02 authority, and no execution authority. Runtime may accept the resource
only when its versions equal a future authentically installed receipt and are
not below its recorded maxima. An absent, malformed, ambiguous, stale, or
rollback-indicating receipt fails closed. This requirement prevents replacement
with an older but otherwise validly signed release. The receipt authority,
design, implementation, and operational validation remain future work;
therefore the trust source is not yet operationally defined.

## 8. Bootstrap-time read semantics

Each bootstrap verification attempt opens and validates the authenticated
bundle, anti-rollback receipt, and resource read-only. It obtains one immutable
descriptor-bound snapshot. It does not cache across attempts and does not
accept a pre-parsed object from the caller.

The verifier selects the sole authenticated key by requiring the signed
bootstrap approval's approver identity and key ID to equal the resource values.
It then applies the already frozen Ed25519, RFC 8785, domain-separator, complete-
binding, validity, and identity-separation rules. The bootstrap record may refer
to the expected key ID, but cannot introduce or override any verification fact.

Read success means only `APPROVER_SIGNATURE_VERIFIED`. It does not mean
`AUTHORIZED`, does not consume authorization, does not create the generic
registry, and does not permit an invocation. The existing bootstrap boundary
must still validate all ceremony bindings, read-only preconditions, durable
single-use consumption, bounded create attempt, postcondition verification,
evidence, and permanent sealing.

## 9. Failure semantics

Before bootstrap authorization consumption, verification denies and performs no
mutation if the bundle, receipt, or resource is absent, ambiguous, malformed,
stale, expired, not-yet-valid, replaced, rolled back, symlinked, hard-linked,
incorrectly owned, incorrectly permissioned, writable, unsealed, signature-
invalid, release-mismatched, digest-mismatched, noncanonical, oversized,
unsupported, multiply keyed, unknown-keyed, or otherwise unverifiable.

Race, I/O ambiguity, clock ambiguity, macOS trust-evaluation ambiguity, receipt
ambiguity, or inability to prove same-descriptor identity also denies. There is
no alternate source, operator override, break-glass key, network fallback,
caller retry authority, or adoption of unverified material. If failure occurs
after the separate bootstrap protocol has durably consumed its authorization,
the existing frozen `FAILED_CONSUMED` or `UNCERTAIN_CONSUMED` terminal semantics
apply unchanged; this trust source creates no retry or recovery path.

## 10. Relationship to the generic SEC-02 trust registry

The bootstrap approver trust source authenticates only the Human Bootstrap
Approver who approves the first creation of
`sec02-human-issuers.v1.json`. The generic registry, once independently created
and sealed under the existing bootstrap protocol, authenticates ordinary human
issuer authorization artifacts. Neither source delegates to the other:

```text
signed Mac release resource
-> verify bootstrap approver signature only
-> existing one-time bootstrap protocol
-> create generic SEC-02 issuer registry once

generic SEC-02 issuer registry
-> verify ordinary authorization artifacts only
-> existing SEC-02 flow
```

The release resource cannot admit ordinary issuers, authorize registry updates,
verify WU09 feature authorization, act as a generic credential store, or execute
anything. The generic registry cannot authenticate initial bootstrap approval
while absent and cannot mutate the release resource.

## 11. Alternatives explicitly rejected

**A separately installed mutable Mac-local trust file** is rejected as the
primary source. If provisioned by the bootstrap operator or accepted merely
because it has local ownership/mode, it permits operator self-authorization and
replacement. If its verifier key is supplied alongside it, it simply moves the
circular trust problem.

**Bootstrap-record, argv, environment, API, CLI, caller, or prospective-issuer
public material** is rejected because it permits caller injection or issuer
self-registration. A digest inside the same record is circular and provides no
independent authenticity.

**The absent or prospective generic SEC-02 registry** is rejected because using
the object being created to authenticate its own creation is circular trust.

**Ubuntu, WU09, Docker, a generic remote command, or a network discovery
service** is rejected because it moves Control Plane authority out of the Mac,
creates mutable discovery/fallback semantics, or introduces an executor where
only verification is allowed.

**Production custody of the Bootstrap Approver private key** is rejected. It
would collapse Approver into Production/operator custody and turn compromise of
the Control Plane into approval manufacture. Only public verification material
may enter the release.

A broad repository key registry is also rejected. One purpose-bound,
single-active-key release resource is smaller, easier to authenticate, and
cannot silently become a generic credential store.

## 12. Why SEC-02 semantics are unchanged

This trust source is strictly before the already frozen one-time bootstrap
protocol and before ordinary Trusted Authorization Intake. It supplies no
Governance object, SEC-02 decision, mutation budget, consumption transition, or
`ControlledExecutionPort` invocation. It neither weakens nor adds an SEC-02
decision state. After initial registry creation, ordinary authorization still
requires the existing generic registry, durable consumption, fresh read-only
preconditions, exact comparison, existing SEC-02
`ALLOW_SINGLE_INVOCATION`, and exactly one bounded feature-specific invocation.

No Governance core, `ControlledExecutionPort`, or WU09 file or semantic change
is required or authorized by this freeze.

## 13. Freeze gates

```text
SEC02_BOOTSTRAP_APPROVER_TRUST_SOURCE_FREEZE_GATE=PASS
SEC02_BOOTSTRAP_APPROVER_TRUST_SOURCE_PRECISION_GATE=PASS
SIGNED_RELEASE_ASSUMPTION_GATE=PASS
INSTALL_POLICY_VS_CURRENT_STATE_GATE=PASS
ANTI_ROLLBACK_AUTHORITY_GATE=PASS
ANTI_ROLLBACK_NO_BOOTSTRAP_AUTHORITY_GATE=PASS
TRUST_SOURCE_INDEPENDENCE_GATE=PASS
PRIVATE_KEY_BOUNDARY_GATE=PASS
CALLER_AUTHORITY_INJECTION_GATE=PASS
OPERATOR_SELF_AUTHORIZATION_GATE=PASS
MAC_CONTROL_PLANE_GATE=PASS
UBUNTU_ZERO_AUTHORITY_GATE=PASS
READ_ONLY_RUNTIME_GATE=PASS
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
SEC02_SEMANTICS_CHANGED=false
GOVERNANCE_CORE_CHANGED=false
CONTROLLED_EXECUTION_PORT_CHANGED=false
WU09_FILES_CHANGED=false
CANONICAL_RERUN_REQUIRED=NO
PRODUCTION_ACCESS_PERFORMED=false
PRODUCTION_MUTATION_PERFORMED=false
PRODUCTION_AUTHORIZATION_CONSUMED=false
DOCKER_RUNTIME_ACCESSED=false
```

`BOOTSTRAP_APPROVER_TRUST_SOURCE_OPERATIONALLY_DEFINED` remains `NO` until a
separately authorized milestone builds and validates the signed-resource
lookup, macOS authenticity evaluation, anti-rollback receipt, read-only
descriptor policy, rotation ceremony, and negative-path tests. The next
milestone after this architecture freeze must be a separate **RELEASE-INSTALL /
ANTI-ROLLBACK AUTHORITY** freeze, or an equivalent release-authenticity
implementation boundary, that defines the receipt's authenticated storage,
update mechanism, and advancing authority. Accordingly,
`SEC02_PRODUCTION_TRUST_BOOTSTRAP_IMPLEMENTATION` is not ready, and this
architecture freeze alone does not make the Production bootstrap available.
