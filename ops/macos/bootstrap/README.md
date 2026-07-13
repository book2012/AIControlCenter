# macOS Bootstrap

This directory contains reusable macOS Control Plane bootstrap and
validation scripts.

## Principles

- Read-only first
- JSON-first output
- Secrets outside Git
- Idempotent scripts
- No application deployment before validation
- No Ubuntu business logic

## Initial Command

Run the read-only macOS inspection:

    bash ops/macos/bootstrap/inspect.sh

## Output

The inspection script writes JSON to standard output.

Example:

    bash ops/macos/bootstrap/inspect.sh \
      | tee "$HOME/Desktop/mac-control-plane-baseline.json"

Validate the generated JSON:

    jq empty "$HOME/Desktop/mac-control-plane-baseline.json"
