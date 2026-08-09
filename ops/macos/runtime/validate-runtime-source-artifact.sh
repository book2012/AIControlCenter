#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(
  cd "$(
    dirname "${BASH_SOURCE[0]}"
  )/../../.." &&
  pwd
)"

PYTHON="${AICONTROLCENTER_CONTROL_PYTHON:-$ROOT/.venv/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
  echo "AIControlCenter control Python unavailable" >&2
  exit 2
fi

exec "$PYTHON" \
  "$ROOT/ops/macos/runtime/runtime-source-artifact.py" \
  validate \
  "$@"
