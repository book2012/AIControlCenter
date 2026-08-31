# SEC-02 Privileged Helper Package Contract

03B4R2-C freezes the app/helper/Mach identifiers, exact bundle layout, two
explicit zero-argument helper methods, native signing resolver, and Secure
Enclave source. Registration remains prohibited and signing remains not ready
until an authoritative Team ID and matching signed artifacts exist.

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

The repository has no authoritative native bundle/signing identity. This
directory provides non-deployable metadata and plist templates for the smallest
future macOS 13+ package boundary:

- one signed AIControlCenter app bundle;
- one bundled LaunchDaemon plist under `Contents/Library/LaunchDaemons`;
- one bounded helper executable under the app bundle;
- `SMAppService.daemon(plistName:)` as the future package API;
- mutually pinned client/helper code-signing requirements configured before
  XPC activation; and
- exactly one semantic XPC operation,
  `RESTRICT_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700`.

No Team ID, designated requirement, bundle identifier, Mach service name,
executable, entitlement, or authorization external form is guessed here. Plist
identity placeholders cannot be packaged until those values are authoritative;
their absence makes runtime readiness `NOT_READY`. The foundation does not register, unregister,
activate, install, start, persist authority, acquire authorization, or mutate a
filesystem.
