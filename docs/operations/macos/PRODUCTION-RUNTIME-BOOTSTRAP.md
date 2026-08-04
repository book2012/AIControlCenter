# Mac Production Python Runtime Bootstrap

## Purpose

Create a commit-specific Python runtime for AIControlCenter on the
Mac mini Control Plane.

## Architecture

Production virtual environments are stored outside the Git repository:

    ~/Library/Application Support/AIControlCenter/runtime/

Each Git commit receives an isolated virtual environment.

Every immutable runtime release requires both:

- `metadata.json`
- `.aicontrolcenter-source-commit`

The marker contains exactly one lowercase 40-character hexadecimal Git SHA and
one trailing newline. The metadata generator validates and atomically publishes
both files before activation. Missing or invalid metadata fails closed, and the
Shadow daemon reads and validates the marker when it starts.

The `current` symbolic link is updated only after:

- Runtime Contract validation
- dependency installation
- application import validation
- Test Suite completion
- generation and validation of both runtime metadata files

Existing immutable releases must not be repaired in place. Build a new release
from committed Git source. Desired state does not authorize changing
`runtime/current` or restarting the service.

## Safety

The bootstrap does not:

- read secret values
- start AIControlCenter
- open a network port
- register launchd
- stop Ubuntu services
- modify the Git working tree

## Run

First regenerate the Runtime Contract for the current commit:

    python3.12 \
      ops/macos/runtime/discover-runtime-contract.py \
      --root "$HOME/AIControlCenter" \
      > "$HOME/Desktop/aicontrolcenter-runtime-contract.json"

Then run:

    bash ops/macos/runtime/bootstrap-production-runtime.sh \
      "$HOME/Desktop/aicontrolcenter-runtime-contract.json" \
      | tee \
        "$HOME/Desktop/aicontrolcenter-production-runtime.json"

## Production Gate

The following field must be true:

    .production_runtime_gate_passed
