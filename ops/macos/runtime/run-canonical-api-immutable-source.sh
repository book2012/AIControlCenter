#!/usr/bin/env bash

set -Eeuo pipefail
umask 077

HOME_DIR="${AICONTROLCENTER_HOME:-$HOME}"
RUN_USER="${AICONTROLCENTER_RUN_USER:-$(/usr/bin/id -un)}"
APPLICATION_ROOT="${AICONTROLCENTER_APPLICATION_ROOT:-$HOME_DIR/Library/Application Support/AIControlCenter}"
RUNTIME_ROOT="$APPLICATION_ROOT/runtime"
VENV_ROOT="$RUNTIME_ROOT/venvs"
CURRENT_RUNTIME="${AICONTROLCENTER_RUNTIME_LINK:-$RUNTIME_ROOT/current}"
DATA_ROOT="${AICONTROLCENTER_DATA_ROOT:-$APPLICATION_ROOT/data}"
HOST="${AICONTROLCENTER_CANONICAL_HOST:-127.0.0.1}"
PORT="${AICONTROLCENTER_CANONICAL_PORT:-58081}"

export HOME="$HOME_DIR"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

if [[ "$(/usr/bin/id -un)" != "$RUN_USER" ]]; then
  echo "Unexpected runtime user" >&2
  exit 78
fi

if [[ ! -L "$CURRENT_RUNTIME" ]]; then
  echo "Current production runtime is not active" >&2
  exit 78
fi

RUNTIME_TARGET="$(/usr/bin/readlink "$CURRENT_RUNTIME")"
if [[ "$RUNTIME_TARGET" != /* ]]; then
  RUNTIME_TARGET="$RUNTIME_ROOT/$RUNTIME_TARGET"
fi

if [[ ! -d "$RUNTIME_TARGET" ]]; then
  echo "AIControlCenter runtime release is unavailable" >&2
  exit 78
fi
if [[ ! -d "$VENV_ROOT" || -L "$VENV_ROOT" ]]; then
  echo "AIControlCenter runtime venv root is unavailable" >&2
  exit 78
fi
VENV_ROOT_REAL="$(cd "$VENV_ROOT" && /bin/pwd -P)"
RUNTIME_REAL="$(cd "$RUNTIME_TARGET" && /bin/pwd -P)"
if [[ "${RUNTIME_REAL%/*}" != "$VENV_ROOT_REAL" ]]; then
  echo "AIControlCenter runtime release escaped runtime venv root" >&2
  exit 78
fi

RUNTIME_ID="$(/usr/bin/basename "$RUNTIME_REAL")"
case "$RUNTIME_ID" in
  ????????????) ;;
  *) echo "AIControlCenter runtime release identity is invalid" >&2; exit 78 ;;
esac
if ! printf '%s\n' "$RUNTIME_ID" | /usr/bin/grep -Eq '^[0-9a-f]{12}$'; then
  echo "AIControlCenter runtime release identity is invalid" >&2
  exit 78
fi

PYTHON_PATH="$RUNTIME_REAL/bin/python"
SOURCE_ROOT="$RUNTIME_ROOT/sources/$RUNTIME_ID"
SOURCE_MARKER="$SOURCE_ROOT/.aicontrolcenter-source-commit"
RUNTIME_MARKER="$RUNTIME_REAL/.aicontrolcenter-source-commit"
VALIDATOR="$SOURCE_ROOT/ops/macos/runtime/runtime-source-artifact.py"

if [[ ! -x "$PYTHON_PATH" || ! -d "$SOURCE_ROOT" || -L "$SOURCE_ROOT" ]]; then
  echo "AIControlCenter immutable runtime/source is unavailable" >&2
  exit 78
fi
if [[ ! -f "$SOURCE_MARKER" || ! -f "$RUNTIME_MARKER" || ! -f "$VALIDATOR" || ! -f "$SOURCE_ROOT/ops/macos/runtime/application.py" ]]; then
  echo "AIControlCenter canonical source identity is unavailable" >&2
  exit 78
fi
if [[ ! -d "$DATA_ROOT" || -L "$DATA_ROOT" ]]; then
  echo "AIControlCenter data root is unavailable" >&2
  exit 78
fi

SOURCE_COMMIT="$(/usr/bin/tr -d '\r\n[:space:]' < "$SOURCE_MARKER")"
RUNTIME_COMMIT="$(/usr/bin/tr -d '\r\n[:space:]' < "$RUNTIME_MARKER")"
if ! printf '%s\n' "$SOURCE_COMMIT" | /usr/bin/grep -Eq '^[0-9a-f]{40}$'; then
  echo "AIControlCenter source commit metadata is invalid" >&2
  exit 78
fi
if [[ "$RUNTIME_COMMIT" != "$SOURCE_COMMIT" ]]; then
  echo "AIControlCenter runtime/source identity mismatch" >&2
  exit 78
fi

unset PYTHONPATH

"$PYTHON_PATH" -P "$VALIDATOR" validate \
  --runtime-root "$RUNTIME_ROOT" \
  --runtime-id "$RUNTIME_ID" \
  --expected-source-commit "$SOURCE_COMMIT" >/dev/null

export AICONTROLCENTER_DATA_ROOT="$DATA_ROOT"
export AICONTROLCENTER_SOURCE_COMMIT="$SOURCE_COMMIT"
export AICONTROLCENTER_RUNTIME_RELEASE="$RUNTIME_ID"
export PYTHONPATH="$SOURCE_ROOT"

cd "$SOURCE_ROOT"
exec "$PYTHON_PATH" -P -m uvicorn ops.macos.runtime.application:app \
  --host "$HOST" \
  --port "$PORT"
