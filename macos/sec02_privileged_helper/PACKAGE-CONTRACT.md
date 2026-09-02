# SEC-02 Privileged Helper Package Contract

## R2-C5A credential input boundary

Commit `ef0df21` validates
`PRODUCTION_SIGNING_CREDENTIAL_CEREMONY_FOUNDATION_VALIDATED`. The C5A boundary
is read-only and metadata-only: it requires an explicit absolute path with exact
lowercase `.p12` or `.pfx`, rejects lexical dot components and symlink traversal,
uses descriptor-relative `openat` plus `O_NOFOLLOW`, and requires the final leaf
to be a regular file owned by the invoking Darwin user with safe permissions and
stable device/inode binding. It never reads credential contents.

This package contract does not import credentials, accept a passphrase through
argv/environment, mutate Keychain, sign or notarize the package, derive concrete
mutual XPC requirements, register/unregister `SMAppService`, or grant remediation
authority. A future Mac-only import is a separate explicit human ceremony with
one attempt and no retry or credential reuse after `FAILED`/`UNCERTAIN`. Even a
successful import requires the C4 verifier before any Production identity or
authoritative Team ID can be established. The package remains unsigned,
unregistered, fail-closed, and not ready for Production or 03B5.

## R2-C4 signing identity inspection boundary

Commit `1cf8648` implements and validates the read-only
`ProductionSigningIdentityVerifier`. Security.framework is primary. Exactly one
fully qualified verified Developer ID Application credential may establish the
authoritative Team ID; multiple qualified valid candidates are ambiguous, while
rejected observations do not create ambiguity. The narrow `/usr/bin/security`
fallback can prove only exact absence and cannot produce `READY`, identity, or
Team ID. Private-key usability is capability evidence, not signing-success proof.

The verifier uses `LAContext.interactionNotAllowed=true`, no pre-authenticated
context, and no `evaluatePolicy()`. It creates, imports, updates, deletes,
exports, or persists no credential; it performs no signing and causes no
Keychain or Production mutation. Focused C4 validation was `8 passed`; native
Swift type-check passed with zero warnings; canonical was `4463 passed, 5
deselected, 675 warnings` and was not rerun for documentation closeout.

This C4 verifier validation is distinct from actual Production identity
verification, signed-package readiness, registration, and remediation / 03B5
readiness. Live Developer ID Application is absent, no authoritative Team ID is
available, and the package remains unsigned and unregistered.

03B4R2-C freezes the app/helper/Mach identifiers, exact bundle layout, two
explicit zero-argument helper methods, native signing resolver, and Secure
Enclave source. Registration remains prohibited and signing remains not ready
until an authoritative Team ID and matching signed artifacts exist.

R2-C3 implementation commit `85b9e32` (`feat: build unsigned SEC-02 native
package`) now backs the exact package allowlist with real, non-empty arm64 thin
Mach-O app and helper executables. The helper's `Helper-Info.plist` is embedded
in `__TEXT,__info_plist` and its executable, bundle identifier, and `BNDL` type
were validated. Neither executable contains `LC_CODE_SIGNATURE`; linker ad-hoc
signing is disabled and no signing occurred. This establishes
`SEC02_UNSIGNED_NATIVE_PACKAGE_VALIDATED`, not signed-package readiness.

The helper strongly owns its XPC delegate and applies the incoming signing
requirement to the actual connection before resume. Authoritative requirements
remain unresolved/null, so all connections and both fixed operations remain
fail-closed and non-operational. The package is explicitly unsigned,
unregistered, without an authoritative signing identity or Team ID, and not
ready for live Production use. Current validation covers arm64 thin artifacts;
universal/fat Mach-O validation and bit-for-bit reproducibility are not claimed.

Current R2-C2 evidence establishes only native source type-check compatibility:
`NativeFoundation.swift` succeeds under `/Library/Developer/CommandLineTools`
with Apple Swift `6.3.3` and macOS SDK `26.5`
(`NATIVE_TYPECHECK_RC=0`, `NATIVE_TOOLCHAIN_COMPATIBLE=YES`,
`SECURE_ENCLAVE_PROVISIONER_TYPECHECKED=YES`). Full Xcode is not established.
Signing discovery found `0 valid identities`, Developer ID Application is absent
(count `0`), the user keychain search list contains only `login.keychain-db`,
and the authoritative Team ID is unresolved. The signed package is not ready;
no registration, live fresh-human approval, trusted-issuer operation, or
governance remediation was performed.

The repository has no authoritative signing identity. This directory provides
metadata, plist templates, and the validated unsigned native artifacts for the
smallest future macOS 13+ package boundary:

- one future signed AIControlCenter app bundle, currently validated unsigned;
- one bundled LaunchDaemon plist under `Contents/Library/LaunchDaemons`;
- one bounded helper executable under the app bundle;
- `SMAppService.daemon(plistName:)` as the future package API;
- mutually pinned client/helper code-signing requirements configured before
  XPC activation; and
- exactly two fixed zero-argument XPC operations: journal provisioning and
  `RESTRICT_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700`.

No Team ID, designated requirement, entitlement, or authorization external form
is guessed here. Frozen repository identifiers do not establish signing
authority; its absence makes runtime readiness `NOT_READY`. The foundation does
not register, unregister, activate, install, start, persist authority, acquire
authorization, or mutate a filesystem.
## R2-C6B external credential acquisition readiness boundary

C6B classifies non-secret future-acquisition metadata only. Eventual C5A/C5B
progression requires a represented Apple Developer ID Application credential
with a represented matching private key. All other credential classes and
invented or Xcode-derived Team ID authority claims fail closed. This readiness
result is not credential proof or ceremony authorization. It is Mac-only,
repository-only, read-only, grants Ubuntu no authority, performs no mutation,
and always emits a null authoritative Team ID until C4 verifies a live identity.
