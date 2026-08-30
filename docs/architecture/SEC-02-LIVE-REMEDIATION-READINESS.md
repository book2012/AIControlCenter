# SEC-02 Live Remediation Readiness

## R2-C1 hardened source, still not live

Static signing metadata is never validity evidence: Security.framework must
successfully validate the complete static artifact and all architectures before
identifier, Team ID, flags, or designated requirement are trusted. Key discovery
is exact-one/fail-closed and future creation requires verified absence; no
duplicate, replacement, repair, deletion, rotation, or retry authority exists.
The protocol algorithm ID, public fingerprint format, and strict journal receipt
are frozen. These changes do not supply Xcode, identities, Team ID, enrollment,
authentication, signed binaries, registration, journal provisioning, or an
operational helper. Live remediation remains `NOT_READY`.

## Composite boundary correction

Repository orchestration now treats bounded Authorization Services acquisition
and exact `FreshHumanEvidenceV1` verification as independent mandatory gates.
Authorization Services `ACQUIRED` with truthful freshness `NOT_VERIFIABLE` may
satisfy only the bounded-right gate. Fresh-human evidence may satisfy only the
verification gate. Neither permits execution unless the existing durable journal
claim also succeeds. This is repository implemented, not live or operational.
The bounded validation result contains no attempt authority or claim capability;
FHE verification likewise creates none. The exact attempt is created as claimed
only after the durable replay claim succeeds.
Python `_TRUSTED_RESOLUTION_MARKER` privacy is not cryptographic identity; actual
Production trust still requires native code-signing resolution and validation.

## Fresh-human evidence update — 2026-08-31

The repository now verifies an exact, bounded, RFC 8785-canonical human-evidence
challenge before the durable replay claim. The future signer is Secure Enclave
P-256 protected by `userPresence` and `privateKeyUsage`, with no reusable
authenticated `LAContext`. This is source-implemented and type-checked only.
The live key, authentication, trusted key enrollment, concrete mutual XPC signing
requirements, helper activation, journal provisioning, and Production ceremony
remain absent; live remediation is therefore `NOT_READY`.

Status: **ARCHITECTURE REVIEWED; NOT READY FOR PRODUCTION CEREMONY**

## SEC02-FS-MACRO-03B4R2-A repository closure

Repository evidence establishes `com.aicontrolcenter` as the authoritative
namespace, but establishes no app/helper bundle identifier, Team ID, Mach
service identifier, or release signing identity. The repository now supplies
non-deployable plist templates and layout metadata with unresolved identity
slots. Both XPC peers require separate concrete requirements; missing,
wildcard/permissive, or role-collapsed requirements fail closed.

The frozen replay separator is implemented with CryptoKit SHA-256 before the
future Python/domain crossing. Synthetic primitive tests match Python exactly;
raw external-form bytes are absent from durable models. Isolated module-cache
Swift type-check passed. Full native toolchain readiness remains `NO`: the
selected directory is `/Library/Developer/CommandLineTools`, and `xcodebuild`
reports that full Xcode is unavailable.

Journal provisioning is repository implemented as exact-target, create-only,
purpose-specific policy with a fakeable adapter boundary. It has no caller path,
remediation, chmod/chown repair, delete/reset/retry, or generic root authority.
Operational provisioning remains `NO`.

R2-B must define an evidence input and verifier result bound together to exact
purpose, exact bounded mutation, exact request identity, a verifier-issued
nonce/challenge, and a freshness window or one-use state. Verification must deny
replay, cross-purpose use, mutation substitution, request substitution, and
authority reuse. The mechanism remains subordinate to the Mac mini Control
Plane and must not become another Control Plane. No cryptographic or platform
mechanism is selected here.

`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

## SEC02-FS-MACRO-03B4R read-only evidence

The exact baseline was `e707d72e89b9288f541af3a071de915ce38c3ee6` on
`feature/homepage-product-management-console`, clean and synchronized at 0/0.
No Production metadata access or mutation occurred. The prior canonical result
is reused: `4408 passed, 5 deselected, 627 warnings`.

Observed host/toolchain facts:

- macOS `26.5.2`, build `25F84`.
- selected developer directory `/Library/Developer/CommandLineTools`;
  `xcodebuild -version` fails because it is not a full Xcode installation.
- Swift and swiftc `/Library/Developer/CommandLineTools/usr/bin/swift` and
  `/Library/Developer/CommandLineTools/usr/bin/swiftc`, both Apple Swift `6.3.3`
  (`swiftlang-6.3.3.1.3 clang-2100.1.1.101`).
- SDK `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`, version `26.5`.
- type-check failed because SDK modules were built with Apple Swift `6.3.2`
  (`swiftlang-6.3.2.1.2 clang-2100.0.123.2`) while the compiler is `6.3.3`;
  the sandbox also denied the default module-cache path.
- codesigning inspection reported `0 valid identities found`.

The repository has no SEC-02 native `.app` target, `Info.plist`, bundled
LaunchDaemon plist, bounded helper executable target, Mach service definition,
entitlements, code-signing configuration, authoritative bundle identifiers, or
concrete client/helper signing requirements. Source contracts are not a built,
signed, registered, installed, started, or operational package.

## Mutual XPC, replay, and fresh approval

The helper must authenticate AIControlCenter and AIControlCenter must
authenticate the helper using concrete code-signing requirements. PID, UID,
process name, filesystem path, and caller-supplied bundle identifier are not
sufficient. Because authoritative signing and bundle identities are absent, no
requirement strings are derived or invented.

The replay direction remains `AuthorizationRef` to
`AuthorizationMakeExternalForm`, ephemeral native bytes, domain-separated
SHA-256, then `AuthorizationReplayKey` across the Python/domain boundary. Raw
external-form bytes must never enter disk, SQLite, JSON, logs, audit payloads,
application state, or caches. The cryptographic contract is defined, but native
derivation is absent, not type-checked, and not operationally validated.

The SDK says `InteractionAllowed` permits interaction when required; it does
not attest that fresh human authentication happened for the exact invocation.
Authorization success, `DestroyRights`, or a new reference cannot independently
produce `FreshApprovalEvidence.VERIFIED`. A separate authoritative fresh-human
evidence mechanism is required. The future exact right remains
`com.aicontrolcenter.governance-remediation.mode-0755-to-0700`.
Preauthorization, partial rights, shared credentials, username/password
injection, reference reuse, and automatic retry remain denied.

## Production journal provisioning architecture

The frozen path is `/Library/Application Support/AIControlCenter/Security/PreBootstrapRemediation/attempt-journal.sqlite3`.
It is a root-owned, purpose-bound evidence store whose sole live mutation writer
is the bounded helper. AIControlCenter retains orchestration/policy and gains no
unrestricted root filesystem authority. The journal stores no raw capability
and grants no execution authority.

`PRE_BOOTSTRAP_REMEDIATION_JOURNAL_PROVISIONING_AUTHORITY` is separate from
remediation authorization, Human Bootstrap Approver, ordinary SEC-02 issuance
or consumption, `ControlledExecutionPort`, generic root authority, feature
authority, and Mac Release Installation Authority unless separately reviewed.
Its future contract is create-only at the exact path with exact safe modes: no
arbitrary path/file, recursion, chmod/chown repair, delete/reset, or remediation.
Provisioning and remediation require separate approvals; neither approval may
authorize the other or both mutations. This is defined, not implemented or
ready.

## Independent 03B5 readiness matrix

| Prerequisite | Result | Exact evidence |
|---|---|---|
| Exact eligibility gate | Ready | Repository implemented and previously validated |
| Durable journal semantics | Ready | Repository implemented and temp-path validated |
| Native toolchain | Blocked | Swift 6.3.3 / SDK Swift 6.3.2 mismatch |
| App/helper signing identities | Blocked | Zero valid identities |
| Mutual XPC requirements | Blocked | No authoritative identities or bundle IDs |
| Native app bundle | Blocked | No native app target/package assets |
| LaunchDaemon package | Blocked | No bundled plist/helper/Mach service/entitlements |
| Native replay fingerprint | Blocked | Contract only; no native implementation/type-check/live validation |
| Fresh-human evidence | Blocked | Authorization Services alone does not prove it |
| Journal provisioning | Blocked | Authority defined only |
| Live journal metadata | Blocked | Not inspected; journal remains non-operational |
| Helper operational status | Blocked | No installed/started helper or live XPC request |

Architecture defined != implemented != operationally validated.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`. The next work unit is
`SEC02-FS-MACRO-03B4R2-RESOLVE-VERIFIED-LIVE-BLOCKERS`.

```text
NATIVE_TOOLCHAIN_READY=NO
LIVE_SIGNING_READINESS=NOT_READY
NATIVE_APP_BUNDLE_FOUNDATION_READY=NO
LAUNCHDAEMON_PACKAGE_READY=NO
SMAPPSERVICE_REGISTRATION_READY=NO
CONCRETE_CLIENT_SIGNING_REQUIREMENT_READY=NO
CONCRETE_HELPER_SIGNING_REQUIREMENT_READY=NO
NATIVE_REPLAY_FINGERPRINT_CONTRACT_READY=YES
NATIVE_REPLAY_FINGERPRINT_TYPECHECKED=NO
REPLAY_FINGERPRINT_OPERATIONALLY_VALIDATED=NO
LIVE_FRESH_APPROVAL_VERIFICATION_READY=NO
SEPARATE_FRESH_HUMAN_EVIDENCE_MECHANISM_REQUIRED=YES
PRODUCTION_JOURNAL_OWNERSHIP_ARCHITECTURE_DEFINED=YES
JOURNAL_PROVISIONING_AUTHORITY_DEFINED=YES
JOURNAL_PROVISIONING_AUTHORITY_IMPLEMENTED=NO
JOURNAL_PROVISIONING_AUTHORITY_READY=NO
PRE_BOOTSTRAP_REMEDIATION_JOURNAL_OPERATIONAL=NO
LIVE_PRIVILEGED_HELPER_OPERATIONAL=NO
PRODUCTION_REMEDIATION_AVAILABLE=NO
READY_FOR_03B5_PRODUCTION_CEREMONY=NO
```
# 03B4R2-C update

The native packaging foundation is defined in `SEC-02-LIVE-SECURITY-PACKAGING.md`. It remains unsigned, unregistered, and non-operational; no identity, Team ID, full Xcode, key, journal, or Production authorization was created.
