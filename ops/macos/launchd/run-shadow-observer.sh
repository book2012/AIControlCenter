#!/bin/bash

set -euo pipefail

REPO="/Users/kyouhan/AIControlCenter"

RUNTIME_LINK="/Users/kyouhan/Library/Application Support/AIControlCenter/runtime/current"

RUNTIME="$(
  readlink "$RUNTIME_LINK"
)"

if [[ -z "$RUNTIME" ]]
then
  echo "[FAIL] Current Runtime unavailable" >&2
  exit 1
fi

PYTHON="$RUNTIME/bin/python"

if [[ ! -x "$PYTHON" ]]
then
  echo "[FAIL] Runtime Python unavailable" >&2
  exit 1
fi

cd "$REPO"

exec "$PYTHON" \
  "$REPO/ops/macos/monitoring/observe-shadow-daemon.py"
