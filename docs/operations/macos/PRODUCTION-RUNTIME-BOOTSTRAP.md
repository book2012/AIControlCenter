# Mac Production Python Runtime Bootstrap

## Purpose

Create a commit-specific Python runtime for AIControlCenter on the
Mac mini Control Plane.

## Architecture

Production virtual environments are stored outside the Git repository:

    ~/Library/Application Support/AIControlCenter/runtime/

Each Git commit receives an isolated virtual environment.

The `current` symbolic link is updated only after:

- Runtime Contract validation
- dependency installation
- application import validation
- Test Suite completion

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
