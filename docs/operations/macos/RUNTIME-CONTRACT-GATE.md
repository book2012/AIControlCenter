# AIControlCenter Runtime Contract Gate

## Purpose

Identify the canonical Python runtime contract before creating the
Mac mini production virtual environment.

## Contract

The gate identifies:

- dependency source
- installation command
- application framework
- application import target
- health endpoints
- test command
- environment variable names

## Safety

This gate is read-only.

It does not:

- install dependencies
- create a virtual environment
- read secret values
- start services
- register launchd
- modify Ubuntu services

## Run

    python3.12 \
      ops/macos/runtime/discover-runtime-contract.py \
      --root "$HOME/AIControlCenter" \
      > "$HOME/Desktop/aicontrolcenter-runtime-contract.json"

## Validate

    jq empty \
      "$HOME/Desktop/aicontrolcenter-runtime-contract.json"

## Production Gate

The following value must be true:

    .runtime_contract_gate_passed

A failed or ambiguous contract must be resolved before creating the
production virtual environment.
