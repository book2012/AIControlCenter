#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"
RUNTIME_ROOT="${AICONTROLCENTER_RUNTIME_ROOT:-$HOME/Library/Application Support/AIControlCenter/runtime}"
VENV_ROOT="$RUNTIME_ROOT/venvs"
LOG_ROOT="$RUNTIME_ROOT/logs"
REPORT_ROOT="$RUNTIME_ROOT/reports"

MODE=""
CONTRACT=""
RELEASE_PATH=""
EXPECTED_COMMIT=""
GIT_COMMIT=""
GIT_SHORT=""
DEPENDENCY_FILE=""
RUNTIME_TARGET=""
VENV_PATH=""
STAGING_PATH=""
LOG_DIR=""
PYTHON_PATH=""
REPORT_PATH=""
CURRENT_STEP="initialization"
CURRENT_TARGET_BEFORE=""
CURRENT_TARGET_AFTER=""
ACTIVATED=false
TEST_STATUS="not_started"
IMPORT_STATUS="not_started"
INSTALL_STATUS="not_started"

usage() {
    cat >&2 <<'USAGE'
Usage:
  bootstrap-production-runtime.sh --mode build --contract <contract.json>
  bootstrap-production-runtime.sh --mode activate --release <release-path> --expected-source-commit <40-char-sha>
USAGE
}

parse_arguments() {
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --mode)
                [[ "$#" -ge 2 ]] || { usage; return 64; }
                MODE="$2"
                shift 2
                ;;
            --contract)
                [[ "$#" -ge 2 ]] || { usage; return 64; }
                CONTRACT="$2"
                shift 2
                ;;
            --release)
                [[ "$#" -ge 2 ]] || { usage; return 64; }
                RELEASE_PATH="$2"
                shift 2
                ;;
            --expected-source-commit)
                [[ "$#" -ge 2 ]] || { usage; return 64; }
                EXPECTED_COMMIT="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown argument: $1" >&2
                usage
                return 64
                ;;
        esac
    done

    case "$MODE" in
        build)
            [[ -n "$CONTRACT" && -z "$RELEASE_PATH" && -z "$EXPECTED_COMMIT" ]] || {
                usage
                return 64
            }
            ;;
        activate)
            [[ -z "$CONTRACT" && -n "$RELEASE_PATH" && -n "$EXPECTED_COMMIT" ]] || {
                usage
                return 64
            }
            ;;
        *)
            echo "An explicit valid --mode is required." >&2
            usage
            return 64
            ;;
    esac
}

read_current_target() {
    if [[ -L "$RUNTIME_ROOT/current" ]]; then
        readlink "$RUNTIME_ROOT/current" 2>/dev/null || true
    fi
}

canonical_path() {
    python3 - "$1" <<'PY'
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
}

write_report() {
    local passed="$1"
    local failure_step="$2"
    local result_code="$3"
    local python_version=""
    local pip_version=""
    local package_count=0

    if [[ -x "$PYTHON_PATH" ]]; then
        python_version="$("$PYTHON_PATH" --version 2>&1 || true)"
        pip_version="$("$PYTHON_PATH" -m pip --version 2>&1 || true)"
        package_count="$(
            "$PYTHON_PATH" -m pip list --format=json 2>/dev/null \
                | jq 'length' 2>/dev/null || printf '0'
        )"
    fi

    jq -n \
      --arg schema_version "1.0" \
      --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      --arg mode "$MODE" \
      --arg repository "$ROOT" \
      --arg contract "$CONTRACT" \
      --arg commit "$GIT_COMMIT" \
      --arg commit_short "$GIT_SHORT" \
      --arg dependency_file "$DEPENDENCY_FILE" \
      --arg runtime_target "$RUNTIME_TARGET" \
      --arg runtime_root "$RUNTIME_ROOT" \
      --arg venv_path "$VENV_PATH" \
      --arg current_target_before "$CURRENT_TARGET_BEFORE" \
      --arg current_target_after "$CURRENT_TARGET_AFTER" \
      --arg log_directory "$LOG_DIR" \
      --arg python_version "$python_version" \
      --arg pip_version "$pip_version" \
      --arg install_status "$INSTALL_STATUS" \
      --arg import_status "$IMPORT_STATUS" \
      --arg test_status "$TEST_STATUS" \
      --arg failure_step "$failure_step" \
      --argjson activated "$ACTIVATED" \
      --argjson result_code "$result_code" \
      --argjson package_count "$package_count" \
      --argjson production_runtime_gate_passed "$passed" \
      '{
          schema_version: $schema_version,
          generated_at: $generated_at,
          mode: $mode,
          activated: $activated,
          production_runtime_gate_passed: $production_runtime_gate_passed,
          failure: {step: $failure_step, result_code: $result_code},
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
              current_target: $current_target_after,
              current_target_before: $current_target_before,
              current_target_after: $current_target_after,
              current_unchanged: ($current_target_before == $current_target_after),
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

cleanup_owned_state() {
    if [[ -n "$STAGING_PATH" && -d "$STAGING_PATH" ]]; then
        case "$STAGING_PATH" in
            "$VENV_ROOT"/.staging-*) rm -rf -- "$STAGING_PATH" ;;
        esac
    fi
}

handle_error() {
    local result_code="${1:-$?}"
    trap - ERR
    set +e
    cleanup_owned_state
    CURRENT_TARGET_AFTER="$(read_current_target)"
    write_report false "$CURRENT_STEP" "$result_code"
    exit "$result_code"
}

prepare_runtime_roots() {
    CURRENT_STEP="prepare runtime directories"
    mkdir -p "$VENV_ROOT" "$LOG_ROOT" "$REPORT_ROOT" || return $?
    chmod 700 "$RUNTIME_ROOT" "$VENV_ROOT" "$LOG_ROOT" "$REPORT_ROOT" || return $?
    CURRENT_TARGET_BEFORE="$(read_current_target)"
    CURRENT_TARGET_AFTER="$CURRENT_TARGET_BEFORE"
}

validate_build_inputs() {
    CURRENT_STEP="validate prerequisites"
    command -v jq >/dev/null 2>&1 || return $?
    command -v git >/dev/null 2>&1 || return $?
    command -v python3.12 >/dev/null 2>&1 || return $?
    [[ -d "$ROOT/.git" ]] || return 66
    [[ -f "$CONTRACT" ]] || return 66

    CURRENT_STEP="validate Runtime Contract"
    jq -e '.runtime_contract_gate_passed == true' "$CONTRACT" >/dev/null || return $?
    DEPENDENCY_FILE="$(jq -er '.production_candidate.dependency_file | select(type == "string" and length > 0)' "$CONTRACT")" || return $?
    RUNTIME_TARGET="$(jq -er '.production_candidate.runtime_target | select(type == "string" and length > 0)' "$CONTRACT")" || return $?

    CURRENT_STEP="validate repository"
    GIT_COMMIT="$(git -C "$ROOT" rev-parse HEAD)" || return $?
    [[ "$GIT_COMMIT" =~ ^[0-9a-f]{40}$ ]] || return 65
    GIT_SHORT="${GIT_COMMIT:0:12}"
    [[ "$GIT_COMMIT" == "$(jq -er '.repository.commit' "$CONTRACT")" ]] || return 65
    [[ -z "$(git -C "$ROOT" status --porcelain)" ]] || return 65
    VENV_PATH="$VENV_ROOT/$GIT_SHORT"
    [[ ! -e "$VENV_PATH" && ! -L "$VENV_PATH" ]] || {
        echo "Finalized release already exists: $VENV_PATH" >&2
        return 73
    }
}

build_runtime() {
    CURRENT_STEP="create owned staging release"
    STAGING_PATH="$(mktemp -d "$VENV_ROOT/.staging-$GIT_SHORT.XXXXXX")"
    LOG_DIR="$LOG_ROOT/$GIT_SHORT"
    mkdir -p "$LOG_DIR"
    chmod 700 "$LOG_DIR"
    python3.12 -m venv "$STAGING_PATH" || return $?
    PYTHON_PATH="$STAGING_PATH/bin/python"

    CURRENT_STEP="bootstrap pip"
    "$PYTHON_PATH" -m pip install --upgrade pip setuptools wheel >"$LOG_DIR/pip-bootstrap.log" 2>&1 || return $?

    CURRENT_STEP="install dependencies"
    local dependency_path="$ROOT/$DEPENDENCY_FILE"
    [[ -f "$dependency_path" ]] || return 66
    case "$DEPENDENCY_FILE" in
        pyproject.toml|*/pyproject.toml)
            "$PYTHON_PATH" -m pip install "$(dirname "$dependency_path")" >"$LOG_DIR/dependency-install.log" 2>&1 || return $?
            ;;
        requirements*.txt|*/requirements*.txt)
            "$PYTHON_PATH" -m pip install -r "$dependency_path" >"$LOG_DIR/dependency-install.log" 2>&1 || return $?
            ;;
        *)
            echo "Unsupported dependency file: $DEPENDENCY_FILE" >&2
            return 64
            ;;
    esac
    INSTALL_STATUS="passed"

    CURRENT_STEP="validate dependency contract"
    "$PYTHON_PATH" -m pip check >"$LOG_DIR/dependency-check.log" 2>&1 || return $?
}

validate_runtime() {
    local runtime_path="$1"
    local expected_commit="$2"
    local runtime_python="$runtime_path/bin/python"
    CURRENT_STEP="validate Runtime Python"
    [[ -x "$runtime_python" ]] || {
        echo "Runtime Python is unavailable: $runtime_python" >&2
        return 65
    }
    PYTHON_PATH="$runtime_python"

    CURRENT_STEP="validate runtime metadata and source marker"
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    "$runtime_python" - "$runtime_path" "$expected_commit" <<'PY'
import json
import re
import sys
from pathlib import Path
from core.runtime.metadata import RuntimeMetadata

runtime_dir = Path(sys.argv[1])
expected_commit = sys.argv[2]
if re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None:
    raise SystemExit("Invalid expected source commit")
marker_path = runtime_dir / ".aicontrolcenter-source-commit"
try:
    marker = marker_path.read_bytes()
except OSError as exc:
    raise SystemExit(f"Runtime source marker unavailable: {exc}") from exc
expected_marker = (expected_commit + "\n").encode("ascii")
if marker != expected_marker:
    raise SystemExit("Invalid or mismatched runtime source commit marker")
metadata = RuntimeMetadata(runtime_dir / "metadata.json").status()
if metadata["available"] is not True:
    raise SystemExit(json.dumps(metadata, sort_keys=True))
if metadata["commit"] != expected_commit:
    raise SystemExit("Runtime metadata source commit mismatch")
print(json.dumps(metadata, sort_keys=True))
PY
    local import_status="$?"
    [[ "$import_status" -eq 0 ]] || return "$import_status"
    local identity_status="$?"
    [[ "$identity_status" -eq 0 ]] || return "$identity_status"

    CURRENT_STEP="validate dependency contract"
    "$runtime_python" -m pip check || return $?
}

generate_runtime_metadata() {
    CURRENT_STEP="generate runtime metadata"
    PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    "$PYTHON_PATH" - "$STAGING_PATH" "$GIT_COMMIT" "$GIT_SHORT" >"$LOG_DIR/runtime-metadata.log" 2>&1 <<'PY'
import sys
from pathlib import Path
from core.runtime.metadata_generator import RuntimeMetadataGenerator

RuntimeMetadataGenerator(
    runtime_dir=Path(sys.argv[1]),
    commit=sys.argv[2],
    short_commit=sys.argv[3],
    runtime_mode="shadow",
).write()
PY
}

validate_application_and_tests() {
    CURRENT_STEP="validate application import"
    local module_name="${RUNTIME_TARGET%%:*}"
    local object_name="${RUNTIME_TARGET#*:}"
    [[ "$module_name" != "$RUNTIME_TARGET" && -n "$module_name" && -n "$object_name" ]]
    PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_PATH" - "$module_name" "$object_name" >"$LOG_DIR/application-import.log" 2>&1 <<'PY'
import importlib
import sys
application = getattr(importlib.import_module(sys.argv[1]), sys.argv[2])
print(type(application).__name__)
PY
    IMPORT_STATUS="passed"

    CURRENT_STEP="run Test Suite"
    local test_command normalized
    test_command="$(jq -r '.production_candidate.test_command // ""' "$CONTRACT")"
    normalized="$(printf '%s' "$test_command" | tr '\n\t' '  ' | awk '{$1=$1; print}')"
    case "$normalized" in
        "python -m pytest -q"|"python3 -m pytest -q")
            (cd "$ROOT"; PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_PATH" -m pytest -q) >"$LOG_DIR/test-suite.log" 2>&1 || return $?
            TEST_STATUS="passed"
            ;;
        "") echo "Missing test command in Runtime Contract" >&2; TEST_STATUS="failed"; return 64 ;;
        *) echo "Unsupported test command: $normalized" >&2; TEST_STATUS="failed"; return 64 ;;
    esac
}

finalize_runtime() {
    CURRENT_STEP="finalize immutable runtime"
    [[ ! -e "$VENV_PATH" && ! -L "$VENV_PATH" ]]
    mv -n "$STAGING_PATH" "$VENV_PATH" || return $?
    [[ ! -d "$STAGING_PATH" ]] || {
        echo "Finalized release appeared during finalization: $VENV_PATH" >&2
        return 73
    }
    STAGING_PATH=""
    PYTHON_PATH="$VENV_PATH/bin/python"
}

run_build_mode() {
    prepare_runtime_roots || return $?
    validate_build_inputs || return $?
    build_runtime || return $?
    validate_application_and_tests || return $?
    generate_runtime_metadata || return $?
    validate_runtime "$STAGING_PATH" "$GIT_COMMIT" >"$LOG_DIR/runtime-validation.log" 2>&1 || return $?
    finalize_runtime || return $?
    CURRENT_TARGET_AFTER="$(read_current_target)"
    [[ "$CURRENT_TARGET_BEFORE" == "$CURRENT_TARGET_AFTER" ]] || return 65
    REPORT_PATH="$REPORT_ROOT/$GIT_SHORT-build.json"
}

activate_runtime() {
    prepare_runtime_roots || return $?
    CURRENT_STEP="validate activation request"
    [[ "$EXPECTED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || {
        echo "Expected source commit must be 40 lowercase hexadecimal characters." >&2
        return 64
    }
    local canonical_venv_root canonical_release canonical_repo_venv
    canonical_venv_root="$(canonical_path "$VENV_ROOT")"
    canonical_release="$(canonical_path "$RELEASE_PATH")"
    canonical_repo_venv="$(canonical_path "$ROOT/.venv")"
    [[ "$canonical_release" == "$canonical_venv_root"/* ]] || {
        echo "Release must be under the configured Runtime venv root." >&2
        return 65
    }
    [[ "$canonical_release" != "$canonical_venv_root" ]] || return 65
    [[ "${canonical_release%/*}" == "$canonical_venv_root" ]] || {
        echo "Release must be a finalized direct child of the Runtime venv root." >&2
        return 65
    }
    [[ "${canonical_release##*/}" != .staging-* ]] || return 65
    [[ "$canonical_release" != "$canonical_repo_venv" && "$canonical_release" != "$canonical_repo_venv"/* ]] || {
        echo "The mutable repository .venv cannot be activated." >&2
        return 65
    }
    [[ -d "$canonical_release" && ! -L "$RELEASE_PATH" ]] || {
        echo "Release must be an existing finalized directory, not a symlink." >&2
        return 65
    }

    VENV_PATH="$canonical_release"
    GIT_COMMIT="$EXPECTED_COMMIT"
    GIT_SHORT="${EXPECTED_COMMIT:0:12}"
    validate_runtime "$VENV_PATH" "$EXPECTED_COMMIT" >/dev/null || return $?

    CURRENT_STEP="activate runtime"
    local temporary_link="$RUNTIME_ROOT/.current.$$.tmp"
    trap 'status=$?; rm -f -- "$temporary_link"; handle_error "$status"' ERR
    ln -s "$VENV_PATH" "$temporary_link" || return $?
    mv -f -h "$temporary_link" "$RUNTIME_ROOT/current" || {
        local switch_status="$?"
        rm -f -- "$temporary_link"
        return "$switch_status"
    }
    trap 'handle_error $?' ERR
    CURRENT_TARGET_AFTER="$(read_current_target)"
    [[ "$CURRENT_TARGET_AFTER" == "$VENV_PATH" ]] || return 65
    ACTIVATED=true
    REPORT_PATH="$REPORT_ROOT/$GIT_SHORT-activate.json"
}

main() {
    parse_arguments "$@" || exit $?
    trap 'handle_error $?' ERR
    case "$MODE" in
        build) run_build_mode || handle_error $? ;;
        activate) activate_runtime || handle_error $? ;;
    esac
    CURRENT_STEP="write runtime report"
    write_report true "" 0 | tee "$REPORT_PATH"
    trap - ERR
}

main "$@"
