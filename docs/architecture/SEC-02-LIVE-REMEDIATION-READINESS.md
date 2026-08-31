# SEC-02 Live Remediation Readiness

## SEC02-FS-MACRO-03B4R2-C4 authoritative state

Commit `1cf8648` establishes
`PRODUCTION_SIGNING_IDENTITY_VERIFIER_VALIDATED`. The verifier is read-only and
uses Security.framework as the primary inspection path. A Team ID can become
authoritative only from exactly one fully qualified verified Developer ID
Application credential. Multiple fully qualified valid candidates produce
`AMBIGUOUS / NOT_READY`; invalid, expired, untrusted, invalid-Team-ID, or
otherwise rejected observations do not make one valid qualified candidate
ambiguous. Private-key usability is capability evidence only and does not prove
that a later package-signing operation will succeed.

The narrow `/usr/bin/security` fallback can prove only exact zero-identity
absence and can never produce `READY`, a candidate identity, or a Team ID.
`LAContext.interactionNotAllowed=true`; no pre-authenticated `LAContext` is used
and no `evaluatePolicy()` call exists. The verifier does not create, import,
update, delete, export, or persist credentials; it performs no signing and zero
Keychain or Production mutation.

Evidence: focused C4 `8 passed`; native Swift type-check `PASS`, zero warnings;
qualified-candidate ambiguity semantics validated; deprecated
`kSecUseAuthenticationUIFail` / `kSecUseAuthenticationUI` absent; canonical
`4463 passed, 5 deselected, 675 warnings`. No canonical rerun was required or
performed for this documentation-only closeout.

The independent readiness stages are: (1) C2 source/toolchain compatibility,
(2) C3 real unsigned native package validation, (3) C4 verifier validation,
(4) actual Production signing identity verification, (5) signed package
readiness, (6) `SMAppService` registration, and (7) Production remediation / 03B5
readiness. Stages 1–3 are complete; stages 4–7 are not.

```text
SEC02_FS_MACRO_03B4R2_C4_IMPLEMENTATION=COMPLETE
PRODUCTION_SIGNING_IDENTITY_VERIFIER_IMPLEMENTED=YES
PRODUCTION_SIGNING_IDENTITY_VERIFIER_VALIDATED=YES
LIVE_DEVELOPER_ID_APPLICATION_STATE=ABSENT
AUTHORITATIVE_TEAM_ID_AVAILABLE=NO
PRODUCTION_SIGNING_IDENTITY_VERIFIED=NO
SIGNED_PACKAGE_READY=NO
LIVE_SIGNING_READINESS=NOT_READY
SMAPPSERVICE_REGISTRATION_OPERATIONAL=NO
PRODUCTION_REMEDIATION_AVAILABLE=NO
READY_FOR_03B5_PRODUCTION_CEREMONY=NO
CANONICAL_RERUN_REQUIRED=NO
```

Mac remains the sole Control Plane. The verifier grants no Production mutation
authority, and Ubuntu receives zero signing, governance, or Production authority.

## SEC02-FS-MACRO-03B4R2-C3 current state

Commit `85b9e32` (`feat: build unsigned SEC-02 native package`) establishes
`SEC02_UNSIGNED_NATIVE_PACKAGE_VALIDATED`. The exact allowlisted package is
backed by real, non-empty arm64 thin Mach-O app/helper executables. Helper
metadata is embedded and validated; delegate lifetime is explicitly strongly
owned; and the unresolved incoming signing requirement is installed on each
actual XPC connection before resume. Neither executable contains
`LC_CODE_SIGNATURE`, linker ad-hoc signing is disabled, and no signing occurred.

Readiness stages remain distinct: C2 source type-check compatibility; synthetic
temporary layout validation; C3 real unsigned native executable/package
validation; signed package readiness; and operational/live Production readiness.
Only the first three are established. Current artifact inspection is arm64-thin
only; universal/fat validation and bit-for-bit reproducibility are not claimed.
Evidence: focused `22 passed`; canonical `4455 passed, 5 deselected, 659
warnings`.

Developer ID Application and authoritative Team ID remain unavailable. The
package remains unsigned, unregistered, and non-operational; requirements remain
unresolved/null, so every incoming XPC connection fails closed and the exactly
two fixed helper operations cannot operate. No Production journal provisioning,
governance remediation, Secure Enclave Production key creation, or Production
mutation occurred. Mac remains the sole Control Plane; Ubuntu receives no
authority; signing grants no mutation authority; and each bounded Production
mutation still requires one fresh human authorization.

```text
DEVELOPER_ID_APPLICATION_AVAILABLE=NO
AUTHORITATIVE_TEAM_ID_AVAILABLE=NO
SIGNED_PACKAGE_READY=NO
LIVE_SIGNING_READINESS=NOT_READY
SMAPPSERVICE_REGISTRATION_OPERATIONAL=NO
SEC02_TRUSTED_ISSUER_OPERATIONAL=NO
PRODUCTION_REMEDIATION_AVAILABLE=NO
READY_FOR_03B5_PRODUCTION_CEREMONY=NO
FULL_XCODE_ESTABLISHED=NO
```

## SEC02-FS-MACRO-03B4R2-C2 current state

`NativeFoundation.swift` type-check now succeeds using
`/Library/Developer/CommandLineTools`, Apple Swift `6.3.3`, and macOS SDK
`26.5`: `NATIVE_TYPECHECK_RC=0`, `NATIVE_TOOLCHAIN_COMPATIBLE=YES`, and
`SECURE_ENCLAVE_PROVISIONER_TYPECHECKED=YES`. This follows implementation
correction commit `51e9a96` (`fix: compile SEC-02 native signing flags`). The
canonical deployment regression is `4449 passed, 5 deselected, 651 warnings`.

This is not a Full Xcode claim and does not make signing ready. Code-signing
identity discovery found `0 valid identities`; Developer ID Application is
absent (count `0`), the user keychain search list is `login.keychain-db` only,
and the authoritative Team ID is unresolved. The signed native package is not
ready. `SMAppService` registration, live fresh-human approval, and governance
remediation were not performed. The SEC-02 trusted issuer is not operational.

Mac remains the sole Control Plane. Signing readiness grants no Production
mutation authority, one fresh human authorization remains required per bounded
Production mutation, and Ubuntu receives no authority.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

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
- the earlier type-check mismatch was corrected by implementation commit
  `51e9a96`; current native type-check return code is `0` and the toolchain is
  compatible for this source check.
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
application state, or caches. The cryptographic contract and native derivation
source are implemented and type-checked, but are not operationally validated.

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
| Native source/toolchain compatibility | Ready for type-check only | Command Line Tools, Swift 6.3.3, SDK 26.5; RC 0 |
| App/helper signing identities | Blocked | Zero valid identities |
| Mutual XPC requirements | Blocked | No authoritative identities or bundle IDs |
| Native app bundle | Blocked | No native app target/package assets |
| LaunchDaemon package | Blocked | No bundled plist/helper/Mach service/entitlements |
| Native replay fingerprint | Partially ready | Native source implemented and type-checked; no live validation |
| Fresh-human evidence | Blocked | Authorization Services alone does not prove it |
| Journal provisioning | Blocked | Authority defined only |
| Live journal metadata | Blocked | Not inspected; journal remains non-operational |
| Helper operational status | Blocked | No installed/started helper or live XPC request |

Architecture defined != implemented != operationally validated.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`. The next work unit is
`SEC02-FS-MACRO-03B4R2-RESOLVE-VERIFIED-LIVE-BLOCKERS`.

```text
NATIVE_TYPECHECK_RC=0
NATIVE_TOOLCHAIN_COMPATIBLE=YES
SECURE_ENCLAVE_PROVISIONER_TYPECHECKED=YES
FULL_XCODE_ESTABLISHED=NO
LIVE_SIGNING_READINESS=NOT_READY
NATIVE_APP_BUNDLE_FOUNDATION_READY=NO
LAUNCHDAEMON_PACKAGE_READY=NO
SMAPPSERVICE_REGISTRATION_READY=NO
CONCRETE_CLIENT_SIGNING_REQUIREMENT_READY=NO
CONCRETE_HELPER_SIGNING_REQUIREMENT_READY=NO
NATIVE_REPLAY_FINGERPRINT_CONTRACT_READY=YES
NATIVE_REPLAY_FINGERPRINT_TYPECHECKED=YES
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
