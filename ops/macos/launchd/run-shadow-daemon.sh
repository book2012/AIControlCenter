#!/usr/bin/env bash

set -eu

WORKER_ENV_FILE="${AICONTROLCENTER_WORKER_ENV_FILE:-/Library/Application Support/AIControlCenter/worker.env}"

if [ -f "$WORKER_ENV_FILE" ]; then
  OWNER="$(stat -f "%Su" "$WORKER_ENV_FILE")"
  MODE="$(stat -f "%OLp" "$WORKER_ENV_FILE")"

  if [ "$OWNER" != "root" ]; then
    echo "[FAIL] Worker environment must be owned by root" >&2
    exit 1
  fi

  case "$MODE" in
    600|400)
      ;;
    *)
      echo "[FAIL] Worker environment permissions must be 600 or 400" >&2
      exit 1
      ;;
  esac

  set -a
  . "$WORKER_ENV_FILE"
  set +a
fi

set -Eeuo pipefail

umask 077

ROOT="${AICONTROLCENTER_ROOT:-/Users/kyouhan/AIControlCenter}"
HOME_DIR="${AICONTROLCENTER_HOME:-/Users/kyouhan}"
RUN_USER="${AICONTROLCENTER_RUN_USER:-kyouhan}"

RUNTIME_ROOT="$HOME_DIR/Library/Application Support/AIControlCenter/runtime"
CURRENT_RUNTIME="$RUNTIME_ROOT/current"

HOST="${AICONTROLCENTER_SHADOW_HOST:-127.0.0.1}"
PORT="${AICONTROLCENTER_SHADOW_PORT:-18100}"

export HOME="$HOME_DIR"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export AICONTROLCENTER_MODE="shadow-read-only"

if [[ "$(/usr/bin/id -un)" != "$RUN_USER" ]]
then
    echo "Unexpected runtime user" >&2
    exit 78
fi

if [[ ! -d "$ROOT/.git" ]]
then
    echo "AIControlCenter repository not found" >&2
    exit 78
fi

if [[ ! -L "$CURRENT_RUNTIME" ]]
then
    echo "Current production runtime is not active" >&2
    exit 78
fi

RUNTIME_TARGET="$(
    /usr/bin/readlink "$CURRENT_RUNTIME"
)"

if [[ "$RUNTIME_TARGET" != /* ]]
then
    RUNTIME_TARGET="$RUNTIME_ROOT/$RUNTIME_TARGET"
fi

PYTHON_PATH="$RUNTIME_TARGET/bin/python"

if [[ ! -x "$PYTHON_PATH" ]]
then
    echo "Current runtime Python is unavailable" >&2
    exit 78
fi

EXPECTED_COMMIT="$(
    /usr/bin/git \
      -C "$ROOT" \
      rev-parse --short=12 HEAD
)"

if [[ "${RUNTIME_TARGET##*/}" != "$EXPECTED_COMMIT" ]]
then
    echo "Runtime commit does not match Git HEAD" >&2
    exit 78
fi

if [[ -n "$(
    /usr/bin/git \
      -C "$ROOT" \
      status --porcelain
)" ]]
then
    echo "Git working tree is not clean" >&2
    exit 78
fi

cd "$ROOT"

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec "$PYTHON_PATH" \
  -m uvicorn \
  core.api.shadow:app \
  --host "$HOST" \
  --port "$PORT"
