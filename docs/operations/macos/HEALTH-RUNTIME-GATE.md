# Mac Read-only Health Runtime Gate

## Purpose

Validate the committed AIControlCenter production runtime on the
Mac mini Control Plane.

## Safety Boundaries

The validation:

- uses the active commit-specific Python runtime
- binds only to 127.0.0.1
- uses a temporary validation port
- calls only a read-only health endpoint
- does not load or print secret values
- does not register launchd
- does not modify Ubuntu
- stops the validation process after completion

## Prerequisites

- Runtime Contract Gate passed
- Production Runtime Gate passed
- current runtime matches the current Git commit
- Git working tree is clean

## Run

    bash ops/macos/runtime/validate-health-runtime.sh \
      "$HOME/Desktop/aicontrolcenter-runtime-contract.json" \
      > "$HOME/Desktop/aicontrolcenter-health-runtime.json" \
      2> "$HOME/Desktop/aicontrolcenter-health-runtime-error.log"

## Production Gate

The following field must be true:

    .production_health_gate_passed

The validation process must be stopped and the port must be released
before the gate can pass.
