#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"

RUNTIME_ROOT="$HOME/Library/Application Support/AIControlCenter/runtime"
CURRENT_RUNTIME="$RUNTIME_ROOT/current"

HOST="${AICONTROLCENTER_SHADOW_HOST:-127.0.0.1}"
PORT="${AICONTROLCENTER_SHADOW_PORT:-18100}"

if [[ ! -d "$ROOT/.git" ]]; then
    echo "AIControlCenter repository not found" >&2
    exit 78
fi

if [[ ! -L "$CURRENT_RUNTIME" ]]; then
    echo "Current production runtime is not active" >&2
    exit 78
fi

RUNTIME_TARGET="$(
    readlink "$CURRENT_RUNTIME"
)"

PYTHON_PATH="$RUNTIME_TARGET/bin/python"

if [[ ! -x "$PYTHON_PATH" ]]; then
    echo "Current runtime Python is unavailable" >&2
    exit 78
fi

EXPECTED_COMMIT="$(
    git -C "$ROOT" \
      rev-parse --short=12 HEAD
)"

if [[ "$(basename "$RUNTIME_TARGET")" != "$EXPECTED_COMMIT" ]]; then
    echo "Runtime commit does not match Git HEAD" >&2
    exit 78
fi

if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
    echo "Git working tree is not clean" >&2
    exit 78
fi

cd "$ROOT"

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
export AICONTROLCENTER_MODE="shadow-read-only"

exec "$PYTHON_PATH" \
  -m uvicorn \
  core.api.shadow:app \
  --host "$HOST" \
  --port "$PORT"
