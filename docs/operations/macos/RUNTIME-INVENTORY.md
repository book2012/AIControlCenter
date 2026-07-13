# AIControlCenter macOS Runtime Inventory

## Purpose

Identify the existing AIControlCenter Python runtime structure before
creating the production virtual environment or launchd services.

## Safety

The inventory is read-only.

It does not:

- install Python packages
- create a virtual environment
- read secret values
- start AIControlCenter
- register launchd services
- modify Ubuntu services

## Inventory Scope

- Python version
- Git branch and commit
- Dependency files
- Candidate Python entrypoints
- API framework indicators
- Test structure
- Docker and runtime configuration
- Existing launchd definitions
- Repository cleanliness

## Run

    bash ops/macos/runtime/inspect-python-runtime.sh \
      | tee "$HOME/Desktop/aicontrolcenter-python-runtime.json"

## Validate

    jq empty \
      "$HOME/Desktop/aicontrolcenter-python-runtime.json"

## Production Rule

No production virtual environment or launchd service is created until
the runtime entrypoint and dependency source are explicitly identified.
