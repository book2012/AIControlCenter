# SEC-02 Privileged Helper Package Contract

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
