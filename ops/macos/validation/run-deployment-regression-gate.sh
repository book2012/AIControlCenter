#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ROOT="$(
  cd "$(
    dirname "${BASH_SOURCE[0]}"
  )/../../.." &&
  pwd
)"

PYTHON="${AICONTROLCENTER_TEST_PYTHON:-$ROOT/.venv/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Deployment test Python unavailable: $PYTHON" >&2
  exit 2
fi

RAW_HARNESS_ROOT="$(
  /usr/bin/mktemp -d \
    "/private/tmp/aicontrolcenter-deployment-gate.XXXXXX"
)"

cleanup() {
  rm -rf "$RAW_HARNESS_ROOT"
}

trap cleanup EXIT INT TERM HUP

HARNESS_ROOT="$(
  "$PYTHON" - "$RAW_HARNESS_ROOT" <<'PY'
from pathlib import Path
import sys

print(
    Path(sys.argv[1]).resolve()
)
PY
)"

case "$HARNESS_ROOT" in
  /private/tmp/*)
    ;;
  *)
    echo "Harness root escaped /private/tmp: $HARNESS_ROOT" >&2
    exit 3
    ;;
esac

BOOTSTRAP_ROOT="$HARNESS_ROOT/bootstrap"
GIT_ROOT="$HARNESS_ROOT/git"
EXECUTION_ROOT="$HARNESS_ROOT/execution"
EXECUTION_HOME="$HARNESS_ROOT/home"
LIVE_ROOT="$HARNESS_ROOT/live"

mkdir -p \
  "$BOOTSTRAP_ROOT" \
  "$GIT_ROOT" \
  "$EXECUTION_ROOT" \
  "$EXECUTION_HOME" \
  "$LIVE_ROOT"

cd "$ROOT"

AICONTROLCENTER_BOOTSTRAP_TEST_ROOT="$BOOTSTRAP_ROOT" \
AICONTROLCENTER_GIT_EVIDENCE_TEST_ROOT="$GIT_ROOT" \
AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_ROOT="$EXECUTION_ROOT" \
AICONTROLCENTER_OPERATIONAL_EXECUTION_TEST_HOME="$EXECUTION_HOME" \
AICONTROLCENTER_OPERATIONAL_LIVE_TEST_ROOT="$LIVE_ROOT" \
PYTHONNOUSERSITE=1 \
PYTHONDONTWRITEBYTECODE=1 \
"$PYTHON" \
  -m pytest "$@"
