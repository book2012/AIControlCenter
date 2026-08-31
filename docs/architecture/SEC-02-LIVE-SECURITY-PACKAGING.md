# SEC-02 live security packaging foundation

## R2-C4 Production signing identity verifier

Implementation commit `1cf8648` establishes the read-only milestone
`PRODUCTION_SIGNING_IDENTITY_VERIFIER_VALIDATED`. Security.framework is the
primary inspection path. Exactly one fully qualified verified Developer ID
Application credential is required to derive an authoritative Team ID. Multiple
qualified valid candidates are `AMBIGUOUS / NOT_READY`; rejected observations
do not create ambiguity. Private-key usability is capability evidence only.

The narrow `/usr/bin/security` fallback can prove only exact zero-identity
absence and can never produce readiness, identity, or Team ID.
`LAContext.interactionNotAllowed=true`; there is no pre-authenticated context or
`evaluatePolicy()` call. The verifier performs no signing, credential creation,
import, update, deletion, export, persistence, Keychain mutation, or Production
mutation. Evidence: focused C4 `8 passed`; native Swift type-check `PASS` with
zero warnings; canonical `4463 passed, 5 deselected, 675 warnings`. Canonical was
not rerun for this documentation-only closeout.

C2 source/toolchain compatibility, C3 real unsigned package validation, C4
verifier validation, actual Production signing identity verification,
signed-package readiness, `SMAppService` registration, and Production remediation
/ 03B5 readiness remain separate states. Only the first three are established.
Live Developer ID Application is absent; Team ID, verified Production identity,
signed package, live signing, registration, remediation, and 03B5 readiness are
not available. Mac remains the sole Control Plane; Ubuntu receives no authority.

Status: C4 read-only verifier implementation validated; C2 native source
type-check and C3 real unsigned arm64 thin Mach-O package validation preserved;
unsigned; unregistered; non-operational.
`READY_FOR_03B5_PRODUCTION_CEREMONY=NO`.

## R2-C3 verified current state

Implementation commit `85b9e32` (`feat: build unsigned SEC-02 native package`)
establishes `SEC02_UNSIGNED_NATIVE_PACKAGE_VALIDATED`. Both executable slots
contain real, non-empty arm64 thin Mach-O artifacts and the exact outer package
allowlist is preserved. The helper embeds `Helper-Info.plist` in
`__TEXT,__info_plist`, validated as executable
`SEC02GovernanceRemediationHelper`, identifier
`com.aicontrolcenter.sec02-remediation-helper`, and package type `BNDL`.
Neither executable has `LC_CODE_SIGNATURE`; linker ad-hoc signing is explicitly
disabled and no `codesign` operation occurred. JSON `signed=false` is supported
by built-artifact inspection.

The helper runtime strongly owns its listener delegate. The incoming XPC signing
requirement is applied to the actual `NSXPCConnection` before `resume()`. Since
authoritative requirements remain unresolved/null, every connection remains
fail-closed. Exactly two fixed operations remain non-operational. Evidence:
focused `22 passed`; canonical `4455 passed, 5 deselected, 659 warnings`.

C2 remains historical evidence for source/toolchain type-check compatibility;
its synthetic temporary layout validation is not rewritten as a native build.
C3 establishes the real unsigned native package only. Signed package and
operational/live Production readiness remain unavailable. Validation covers the
current arm64 thin artifacts; universal/fat validation and bit-for-bit
reproducibility are not claimed.

No `SMAppService` registration/unregistration, Production journal provisioning,
governance remediation, Secure Enclave Production key creation, or Production
mutation occurred. Developer ID Application, authoritative Team ID, signed
package, live signing, trusted issuer operation, Production remediation, 03B5
ceremony readiness, and Full Xcode remain unavailable.

## R2-C2 verified current state

`NativeFoundation.swift` now type-checks using
`/Library/Developer/CommandLineTools`, Apple Swift `6.3.3`, and macOS SDK
`26.5`. Exact evidence: `NATIVE_TYPECHECK_RC=0`,
`NATIVE_TOOLCHAIN_COMPATIBLE=YES`, and
`SECURE_ENCLAVE_PROVISIONER_TYPECHECKED=YES`. The implementation correction is
commit `51e9a96` (`fix: compile SEC-02 native signing flags`). The canonical
deployment regression is `4449 passed, 5 deselected, 651 warnings`.

Full Xcode is not established. Code-signing identity discovery returned `0
valid identities`; Developer ID Application is absent, with count `0`. The user
keychain search list contains `login.keychain-db` only, and the authoritative
Team ID remains unresolved. Consequently, the signed native package is not
ready. `SMAppService` registration, live fresh-human approval, and governance
remediation were not performed; the SEC-02 trusted issuer is not operational.

Mac remains the sole Control Plane. Signing readiness does not grant Production
mutation authority. Each bounded Production mutation still requires one fresh
human authorization. Ubuntu receives no authority.

## R2-C1 validity and readiness terminology

`SecCodeCopySigningInformation` is metadata retrieval, not signature validation.
The resolver first runs all-architecture static validity checking and fails closed
on any non-success, then checks exact bundle ID, authoritative Team ID, ad-hoc
flags, and designated requirement. The validator creates empty executable
placeholders, so its result is only `TEMPORARY_PACKAGE_LAYOUT_VALIDATED`; it is
not a native executable build, signed package, SMAppService registration, or
operational helper. The two RPC methods below remain the complete surface, with
no selector, operation argument, generic payload, path, mode, identity, command,
or argv.

## Frozen identity and layout

The app bundle ID is `com.aicontrolcenter.app`. The helper bundle ID and Mach
service are `com.aicontrolcenter.sec02-remediation-helper`; the LaunchDaemon
plist is `com.aicontrolcenter.sec02-remediation-helper.plist`. These repository
names do not establish a Team ID or signing authority.

The only accepted layout is:

```
AIControlCenter.app/Contents/Info.plist
AIControlCenter.app/Contents/MacOS/AIControlCenter
AIControlCenter.app/Contents/MacOS/SEC02GovernanceRemediationHelper
AIControlCenter.app/Contents/Library/LaunchDaemons/com.aicontrolcenter.sec02-remediation-helper.plist
```

The validator rejects placeholders, identifier/executable substitution,
malformed plists, arbitrary destinations, and layout drift. Raw strings never
confer signing readiness.

## Native boundaries

The source fixes `SMAppService.daemon(plistName:)` to the bundled plist and
does not expose registration or unregistration. The signing resolver inspects
signed artifacts and designated requirements, rejects ad-hoc identity,
wildcards, bundle/Team mismatch, and keeps app/helper roles distinct. Only its
role-bound output can configure mutual XPC requirements.

The helper protocol has exactly two zero-argument methods:

1. `provisionPreBootstrapRemediationJournal()`
2. `restrictGovernanceDirectoryMode0755To0700()`

They have typed results and no selector, path, mode, identity, command, or
payload. Each has a distinct control-plane authorization path; one
authorization cannot invoke both.

## Secure Enclave and enrollment

The fixed key tag is
`com.aicontrolcenter.sec02.fresh-human-presence.p256.v1`. Source fixes Secure
Enclave P-256, `WhenUnlockedThisDeviceOnly`, `userPresence`, and
`privateKeyUsage`. It contains no application password, reusable `LAContext`,
software Production fallback, or private-key export. Only public-key bytes are
SHA-256 fingerprinted.

`PRE_BOOTSTRAP_FRESH_HUMAN_KEY_PROVISIONING_AUTHORITY` is a distinct future
purpose. In its separately authorized ceremony, the signed adapter creates the
exact tagged key and persists only the public verification identity/fingerprint
in a purpose-bound record. That record grants no execution authority, is not an
ordinary issuer, cannot be caller-selected or silently replaced, and cannot
authorize journal provisioning, helper registration, or remediation.

## Journal crash and replay contract

`ABSENT` permits one create attempt whose transaction initializes a minimal
receipt: schema/version, purpose, provisioning replay fingerprint, and terminal
state. No raw authorization persists. `SAFE_EXISTING` plus the exact completed
receipt is read-only recognition. `UNSAFE_EXISTING`, `AMBIGUOUS`, and receipt
mismatch fail closed. There is no repair, retry mutation, delete/recreate,
claim stealing, lease expiry, or reset.

## Remaining Production ceremony DAG

1. `C2-1 AUTHORITATIVE_RELEASE_SIGNING_PREREQUISITE`: operator obtains an
   authoritative Developer identity and Team ID.
2. `C2-2 FRESH_HUMAN_SECURE_ENCLAVE_KEY_PROVISIONING`: one authorization and
   one exact key-provisioning/enrollment mutation.
3. `C2-3 SIGNED_HELPER_PACKAGE_AND_REGISTRATION`: sign, resolve mutual
   requirements, then separately authorize registration/approval.
4. `C2-4 PRODUCTION_JOURNAL_PROVISIONING`: one separate authorization and
   exact create-only journal mutation.
5. `03B5 GOVERNANCE_DIRECTORY_REMEDIATION`: fresh separate authorization for
   the exact `0755 -> 0700` mutation.

Repository implemented, source typechecked, package build validated, signed,
registered, and operational are distinct states and must never be collapsed.
