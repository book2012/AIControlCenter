# Mac mini Control Plane Foundation Gate

## Purpose

Validate that the Mac mini is ready to become the production
AIControlCenter Control Plane.

## Scope

The gate validates:

- macOS on Apple Silicon
- FileVault
- Application Firewall
- Stealth Mode
- Xcode Command Line Tools
- Homebrew
- Git and GitHub CLI
- GitHub authentication
- SSH Git protocol
- jq
- Python 3.12
- AIControlCenter repository
- Storefront release candidate tag
- Git working tree status
- AIControlCenter runtime directories

## Safety

This gate is read-only.

It does not:

- install packages
- copy secrets
- start services
- modify launchd
- change firewall settings
- deploy applications

## Run

    bash ops/macos/bootstrap/validate-foundation.sh \
      | tee "$HOME/Desktop/mac-control-plane-foundation-gate.json"

## Validate JSON

    jq empty \
      "$HOME/Desktop/mac-control-plane-foundation-gate.json"

## Show Failed Checks

    jq -r '
      .checks
      | to_entries[]
      | select(.value == false)
      | .key
    ' "$HOME/Desktop/mac-control-plane-foundation-gate.json"

## Production Gate

The following field must be true:

    .production_gate_passed
