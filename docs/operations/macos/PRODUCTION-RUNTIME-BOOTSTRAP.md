# Mac Production Python Runtime Bootstrap

## Purpose and authorization boundary

The canonical builder creates and validates commit-specific Python Runtime
releases on the Mac mini Control Plane. Build and activation are separate,
explicit operations. Neither operation restarts a service, changes launchd or
Caddy, authorizes production, or delegates Control Plane work to Ubuntu.
Production remains `NOT_AUTHORIZED`.

An invocation without `--mode build` or `--mode activate` fails closed. There
is no legacy or implicit activation path.

## Runtime layout and identity

The default Runtime root is:

    "$HOME/Library/Application Support/AIControlCenter/runtime"

Final releases live under `runtime/venvs/`. Each immutable release contains:

- `metadata.json`
- `.aicontrolcenter-source-commit`
- an executable `bin/python`

The marker is exactly one lowercase 40-character Git SHA plus one newline.
Metadata retains its existing schema and meanings. An existing finalized
release is never reinstalled, repaired, or patched in place.

## Build-only flow

First generate the Runtime Contract for the exact clean repository commit:

    python3.12 \
      ops/macos/runtime/discover-runtime-contract.py \
      --root "$HOME/AIControlCenter" \
      > "$HOME/Desktop/aicontrolcenter-runtime-contract.json"

Then explicitly build:

    bash ops/macos/runtime/bootstrap-production-runtime.sh \
      --mode build \
      --contract "$HOME/Desktop/aicontrolcenter-runtime-contract.json" \
      | tee "$HOME/Desktop/aicontrolcenter-runtime-build.json"

Build mode creates one owned staging directory beneath `runtime/venvs`,
installs dependencies only there, validates the application imports and
dependency contract, runs the contract-approved test suite, generates and
validates metadata and the exact source marker, then atomically renames the
staging directory to its final commit-specific path.

The structured report has `mode: "build"`, `activated: false`, and records
`runtime.current_target_before`, `runtime.current_target_after`, and
`runtime.current_unchanged`. The two targets must be identical. Build mode
never changes `runtime/current`.

Validation evidence consists of the successful report, the build logs under
`runtime/logs/<short-commit>/`, valid identity files in the finalized release,
successful Runtime Python and dependency checks, application import evidence,
and test-suite evidence. A failed build removes only its own staging directory.

## Explicit activation

Activation requires a previously finalized release beneath the configured
Runtime venv root and the exact expected full source commit:

    bash ops/macos/runtime/bootstrap-production-runtime.sh \
      --mode activate \
      --release "$HOME/Library/Application Support/AIControlCenter/runtime/venvs/<release>" \
      --expected-source-commit <lowercase-40-character-git-sha> \
      | tee "$HOME/Desktop/aicontrolcenter-runtime-activation.json"

Before switching, activation validates the path boundary, executable Runtime
Python, dependency consistency, metadata availability and commit identity, and
the exact source marker. Paths outside `runtime/venvs`, symlinked release
directories, incomplete releases, and the mutable repository `.venv` fail
closed. Activation does not build, install dependencies, or mutate the chosen
release.

The switch is an atomic replacement symlink rename. A successful report has
`mode: "activate"` and sets `activated: true` only after verifying the new
`runtime/current` target. It also preserves the previous and new targets.

## Rollback boundary

The previous target in the activation report is rollback evidence, not
rollback authorization. Rolling back requires a new, separately authorized
explicit activation of an already validated immutable release. Service restart
is another separate operational gate. This runbook grants neither production
activation nor restart authority.

The mutable repository `.venv` must never be selected, and desired state or a
build report must never be interpreted as activation authorization.
