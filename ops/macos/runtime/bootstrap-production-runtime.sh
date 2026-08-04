#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"
CONTRACT="${1:-$HOME/Desktop/aicontrolcenter-runtime-contract.json}"

RUNTIME_ROOT="$HOME/Library/Application Support/AIControlCenter/runtime"
VENV_ROOT="$RUNTIME_ROOT/venvs"
LOG_ROOT="$RUNTIME_ROOT/logs"
REPORT_ROOT="$RUNTIME_ROOT/reports"

CURRENT_STEP="initialization"
GIT_COMMIT=""
GIT_SHORT=""
DEPENDENCY_FILE=""
RUNTIME_TARGET=""
VENV_PATH=""
LOG_DIR=""
PYTHON_PATH=""
TEST_STATUS="not_started"
IMPORT_STATUS="not_started"
INSTALL_STATUS="not_started"

write_report() {
    local passed="$1"
    local failure_step="$2"
    local result_code="$3"

    local python_version=""
    local pip_version=""
    local package_count=0
    local current_target=""

    if [[ -x "$PYTHON_PATH" ]]; then
        python_version="$(
            "$PYTHON_PATH" --version 2>&1 || true
        )"

        pip_version="$(
            "$PYTHON_PATH" -m pip --version 2>&1 || true
        )"

        package_count="$(
            "$PYTHON_PATH" -m pip list \
                --format=json \
                2>/dev/null \
                | jq 'length' \
                2>/dev/null \
                || printf '0'
        )"
    fi

    if [[ -L "$RUNTIME_ROOT/current" ]]; then
        current_target="$(
            readlink "$RUNTIME_ROOT/current" \
                2>/dev/null \
                || true
        )"
    fi

    jq -n \
      --arg schema_version "1.0" \
      --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      --arg repository "$ROOT" \
      --arg contract "$CONTRACT" \
      --arg commit "$GIT_COMMIT" \
      --arg commit_short "$GIT_SHORT" \
      --arg dependency_file "$DEPENDENCY_FILE" \
      --arg runtime_target "$RUNTIME_TARGET" \
      --arg runtime_root "$RUNTIME_ROOT" \
      --arg venv_path "$VENV_PATH" \
      --arg current_target "$current_target" \
      --arg log_directory "$LOG_DIR" \
      --arg python_version "$python_version" \
      --arg pip_version "$pip_version" \
      --arg install_status "$INSTALL_STATUS" \
      --arg import_status "$IMPORT_STATUS" \
      --arg test_status "$TEST_STATUS" \
      --arg failure_step "$failure_step" \
      --argjson result_code "$result_code" \
      --argjson package_count "$package_count" \
      --argjson production_runtime_gate_passed "$passed" \
      '{
          schema_version: $schema_version,
          generated_at: $generated_at,
          production_runtime_gate_passed:
              $production_runtime_gate_passed,
          failure: {
              step: $failure_step,
              result_code: $result_code
          },
          repository: {
              path: $repository,
              commit: $commit,
              commit_short: $commit_short
          },
          contract: {
              path: $contract,
              dependency_file: $dependency_file,
              runtime_target: $runtime_target
          },
          runtime: {
              root: $runtime_root,
              venv_path: $venv_path,
              current_target: $current_target,
              log_directory: $log_directory,
              python_version: $python_version,
              pip_version: $pip_version,
              installed_package_count: $package_count
          },
          checks: {
              dependency_install: $install_status,
              application_import: $import_status,
              test_suite: $test_status
          },
          safety: {
              secret_values_read: false,
              network_service_started: false,
              launchd_modified: false,
              ubuntu_modified: false
          }
      }'
}

handle_error() {
    local result_code="${1:-$?}"

    trap - ERR
    set +e

    write_report \
      false \
      "$CURRENT_STEP" \
      "$result_code"

    local report_status="$?"

    if [[ "$report_status" -ne 0 ]]; then
        jq -n \
          --arg schema_version "1.0" \
          --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
          --arg failure_step "$CURRENT_STEP" \
          --argjson result_code "$result_code" \
          '{
              schema_version: $schema_version,
              generated_at: $generated_at,
              production_runtime_gate_passed: false,
              failure: {
                  step: $failure_step,
                  result_code: $result_code
              },
              report_generation_failed: true
          }'
    fi

    exit "$result_code"
}

trap 'handle_error $?' ERR

CURRENT_STEP="validate prerequisites"

command -v jq >/dev/null 2>&1
command -v git >/dev/null 2>&1
command -v python3.12 >/dev/null 2>&1

[[ -d "$ROOT/.git" ]]
[[ -f "$CONTRACT" ]]

CURRENT_STEP="validate Runtime Contract"

jq -e \
  '.runtime_contract_gate_passed == true' \
  "$CONTRACT" \
  >/dev/null

DEPENDENCY_FILE="$(
    jq -er \
      '.production_candidate.dependency_file
       | select(type == "string" and length > 0)' \
      "$CONTRACT"
)"

RUNTIME_TARGET="$(
    jq -er \
      '.production_candidate.runtime_target
       | select(type == "string" and length > 0)' \
      "$CONTRACT"
)"

CURRENT_STEP="validate repository"

GIT_COMMIT="$(
    git -C "$ROOT" \
      rev-parse HEAD
)"

GIT_SHORT="$(
    git -C "$ROOT" \
      rev-parse --short=12 HEAD
)"

CONTRACT_COMMIT="$(
    jq -er \
      '.repository.commit' \
      "$CONTRACT"
)"

[[ "$GIT_COMMIT" == "$CONTRACT_COMMIT" ]]
[[ -z "$(git -C "$ROOT" status --porcelain)" ]]

CURRENT_STEP="prepare runtime directories"

VENV_PATH="$VENV_ROOT/$GIT_SHORT"
LOG_DIR="$LOG_ROOT/$GIT_SHORT"

mkdir -p \
  "$VENV_ROOT" \
  "$LOG_DIR" \
  "$REPORT_ROOT"

chmod 700 \
  "$RUNTIME_ROOT" \
  "$VENV_ROOT" \
  "$LOG_ROOT" \
  "$REPORT_ROOT" \
  "$LOG_DIR"

CURRENT_STEP="create virtual environment"

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
    python3.12 -m venv \
      "$VENV_PATH"
fi

PYTHON_PATH="$VENV_PATH/bin/python"

CURRENT_STEP="bootstrap pip"

"$PYTHON_PATH" -m pip install \
  --upgrade \
  pip \
  setuptools \
  wheel \
  >"$LOG_DIR/pip-bootstrap.log" \
  2>&1

CURRENT_STEP="install dependencies"

DEPENDENCY_PATH="$ROOT/$DEPENDENCY_FILE"

[[ -f "$DEPENDENCY_PATH" ]]

case "$DEPENDENCY_FILE" in
    pyproject.toml|*/pyproject.toml)
        INSTALL_ROOT="$(
            dirname "$DEPENDENCY_PATH"
        )"

        "$PYTHON_PATH" -m pip install \
          "$INSTALL_ROOT" \
          >"$LOG_DIR/dependency-install.log" \
          2>&1
        ;;

    requirements*.txt|*/requirements*.txt)
        "$PYTHON_PATH" -m pip install \
          -r "$DEPENDENCY_PATH" \
          >"$LOG_DIR/dependency-install.log" \
          2>&1
        ;;

    *)
        echo \
          "Unsupported dependency file: $DEPENDENCY_FILE" \
          >&2

        false
        ;;
esac

INSTALL_STATUS="passed"

CURRENT_STEP="validate application import"

MODULE_NAME="${RUNTIME_TARGET%%:*}"
OBJECT_NAME="${RUNTIME_TARGET#*:}"

[[ "$MODULE_NAME" != "$RUNTIME_TARGET" ]]
[[ -n "$MODULE_NAME" ]]
[[ -n "$OBJECT_NAME" ]]

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
"$PYTHON_PATH" - \
  "$MODULE_NAME" \
  "$OBJECT_NAME" \
  >"$LOG_DIR/application-import.log" \
  2>&1 <<'PY'
from __future__ import annotations

import importlib
import sys


module_name = sys.argv[1]
object_name = sys.argv[2]

module = importlib.import_module(module_name)
application = getattr(module, object_name)

print(
    f"Imported {module_name}:{object_name} "
    f"as {type(application).__name__}"
)
PY

IMPORT_STATUS="passed"

CURRENT_STEP="run Test Suite"

TEST_COMMAND="$(
    jq -r \
      '.production_candidate.test_command // ""' \
      "$CONTRACT"
)"

TEST_COMMAND_NORMALIZED="$(
    printf '%s' "$TEST_COMMAND" \
      | tr '
	' '   ' \
      | awk '{$1=$1; print}'
)"

case "$TEST_COMMAND_NORMALIZED" in
    "python -m pytest -q"|"python3 -m pytest -q")
        if (
            cd "$ROOT"

            PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
            "$PYTHON_PATH" -m pytest -q
        ) >"$LOG_DIR/test-suite.log" 2>&1
        then
            TEST_STATUS="passed"
        else
            TEST_RESULT="$?"
            TEST_STATUS="failed"

            handle_error "$TEST_RESULT"
        fi
        ;;

    "")
        echo \
          "Missing test command in Runtime Contract" \
          >&2

        TEST_STATUS="failed"

        handle_error 64
        ;;

    *)
        echo \
          "Unsupported test command: $TEST_COMMAND_NORMALIZED" \
          >&2

        TEST_STATUS="failed"

        handle_error 64
        ;;
esac

CURRENT_STEP="generate runtime metadata"

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
"$PYTHON_PATH" - \
  "$VENV_PATH" \
  "$GIT_COMMIT" \
  "$GIT_SHORT" \
  >"$LOG_DIR/runtime-metadata.log" \
  2>&1 <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from core.runtime.metadata import RuntimeMetadata
from core.runtime.metadata_generator import (
    RuntimeMetadataGenerator,
)

runtime_dir = Path(sys.argv[1])
commit = sys.argv[2]
short_commit = sys.argv[3]

generator = RuntimeMetadataGenerator(
    runtime_dir=runtime_dir,
    commit=commit,
    short_commit=short_commit,
    runtime_mode="shadow",
)

metadata_path = generator.write()
metadata = RuntimeMetadata(metadata_path).status()
marker_path = runtime_dir / ".aicontrolcenter-source-commit"
expected_marker = (commit + "\n").encode("ascii")

if metadata["available"] is not True:
    raise SystemExit(
        json.dumps(metadata, sort_keys=True)
    )

if marker_path.read_bytes() != expected_marker:
    raise SystemExit("Invalid runtime source commit marker")

print(
    json.dumps(
        metadata,
        sort_keys=True,
    )
)
PY

CURRENT_STEP="activate runtime"

ln -sfn \
  "$VENV_PATH" \
  "$RUNTIME_ROOT/current"

CURRENT_STEP="write runtime report"

REPORT_PATH="$REPORT_ROOT/$GIT_SHORT.json"

write_report \
  true \
  "" \
  0 \
  | tee "$REPORT_PATH"

trap - ERR
