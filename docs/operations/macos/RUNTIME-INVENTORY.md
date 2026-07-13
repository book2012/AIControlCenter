# AIControlCenter macOS Runtime Inventory

## Purpose

Identify the existing AIControlCenter Python runtime structure before
creating a production virtual environment or launchd service.

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

- Python runtime
- Dependency files
- Candidate entrypoints
- Application frameworks
- Health API indicators
- Test structure
- Environment variable names
- Runtime scripts
- Docker configuration
- Existing launchd definitions

## Run

    bash ops/macos/runtime/inspect-python-runtime.sh \
      | tee "$HOME/Desktop/aicontrolcenter-python-runtime.json"

## Validate

    jq empty \
      "$HOME/Desktop/aicontrolcenter-python-runtime.json"

## Production Rule

No production virtual environment is created until the dependency
source and runtime entrypoint are explicitly identified.
