#!/usr/bin/env bash

set -u -o pipefail

ROOT="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"
CONTRACT="${1:-$HOME/Desktop/aicontrolcenter-runtime-contract.json}"

RUNTIME_ROOT="$HOME/Library/Application Support/AIControlCenter/runtime"
CURRENT_LINK="$RUNTIME_ROOT/current"
LOG_ROOT="$RUNTIME_ROOT/logs"

HOST="${AICONTROLCENTER_HEALTH_HOST:-127.0.0.1}"
PORT="${AICONTROLCENTER_HEALTH_PORT:-18080}"

TIMESTAMP="$(
    date -u '+%Y%m%dT%H%M%SZ'
)"

LOG_DIR="$LOG_ROOT/health-$TIMESTAMP"
SERVER_LOG="$LOG_DIR/server.log"
RESPONSE_FILE="$LOG_DIR/health-response.json"
LISTENER_FILE="$LOG_DIR/listener.txt"

PID=""

# Invoked indirectly by EXIT, INT, and TERM traps.
# shellcheck disable=SC2329
cleanup() {
    if [[ -n "$PID" ]] \
        && kill -0 "$PID" >/dev/null 2>&1
    then
        kill "$PID" >/dev/null 2>&1 || true

        for _ in {1..20}; do
            if ! kill -0 "$PID" >/dev/null 2>&1; then
                break
            fi

            sleep 0.1
        done

        kill -9 "$PID" >/dev/null 2>&1 || true
        wait "$PID" >/dev/null 2>&1 || true
    fi
}

trap cleanup EXIT INT TERM

emit_prerequisite_failure() {
    local step="$1"
    local message="$2"

    jq -n \
      --arg schema_version "1.0" \
      --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
      --arg step "$step" \
      --arg message "$message" \
      --arg repository "$ROOT" \
      --arg contract "$CONTRACT" \
      '{
          schema_version: $schema_version,
          generated_at: $generated_at,
          production_health_gate_passed: false,
          failure: {
              step: $step,
              message: $message
          },
          repository: {
              path: $repository
          },
          contract: {
              path: $contract
          },
          safety: {
              localhost_only: true,
              secret_values_read: false,
              launchd_modified: false,
              ubuntu_modified: false
          }
      }'
}

for command in \
    jq \
    git \
    curl \
    lsof
do
    if ! command -v "$command" >/dev/null 2>&1; then
        emit_prerequisite_failure \
          "validate prerequisites" \
          "Required command missing: $command"

        exit 1
    fi
done

if [[ ! -d "$ROOT/.git" ]]; then
    emit_prerequisite_failure \
      "validate repository" \
      "Git repository not found"

    exit 1
fi

if [[ ! -s "$CONTRACT" ]] \
    || ! jq empty "$CONTRACT" >/dev/null 2>&1
then
    emit_prerequisite_failure \
      "validate contract" \
      "Runtime Contract is missing or invalid"

    exit 1
fi

if ! jq -e \
    '.runtime_contract_gate_passed == true' \
    "$CONTRACT" \
    >/dev/null
then
    emit_prerequisite_failure \
      "validate contract" \
      "Runtime Contract Gate has not passed"

    exit 1
fi

if [[ ! -L "$CURRENT_LINK" ]]; then
    emit_prerequisite_failure \
      "validate runtime" \
      "Current production runtime is not active"

    exit 1
fi

CURRENT_VENV="$(
    readlink "$CURRENT_LINK"
)"

PYTHON_PATH="$CURRENT_VENV/bin/python"

if [[ ! -x "$PYTHON_PATH" ]]; then
    emit_prerequisite_failure \
      "validate runtime" \
      "Current runtime Python is not executable"

    exit 1
fi

CURRENT_COMMIT="$(
    git -C "$ROOT" rev-parse HEAD
)"

CURRENT_SHORT="$(
    git -C "$ROOT" rev-parse --short=12 HEAD
)"

CONTRACT_COMMIT="$(
    jq -r \
      '.repository.commit // ""' \
      "$CONTRACT"
)"

if [[ "$CURRENT_COMMIT" != "$CONTRACT_COMMIT" ]]; then
    emit_prerequisite_failure \
      "validate commit" \
      "Runtime Contract commit does not match Git HEAD"

    exit 1
fi

if [[ "$(basename "$CURRENT_VENV")" != "$CURRENT_SHORT" ]]; then
    emit_prerequisite_failure \
      "validate runtime" \
      "Current runtime does not match Git HEAD"

    exit 1
fi

if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
    emit_prerequisite_failure \
      "validate repository" \
      "Git working tree is not clean"

    exit 1
fi

RUNTIME_TARGET="$(
    jq -r \
      '.production_candidate.runtime_target // ""' \
      "$CONTRACT"
)"

if [[ -z "$RUNTIME_TARGET" ]]; then
    emit_prerequisite_failure \
      "validate contract" \
      "Runtime target is missing"

    exit 1
fi

HEALTH_PATH="$(
    jq -r '
      (
        [
          .production_candidate
          .health_endpoints[]?
          .path
        ]
        | map(select(. == "/health"))
        | .[0]
      )
      //
      (
        .production_candidate
        .health_endpoints[0]
        .path
      )
      //
      "/health"
    ' "$CONTRACT"
)"

mkdir -p "$LOG_DIR"
chmod 700 "$LOG_DIR"

PROCESS_STARTED="false"
HTTP_200="false"
JSON_VALID="false"
JSON_OBJECT="false"
LISTENER_LOCAL_ONLY="false"
PROCESS_STOPPED="false"
PORT_RELEASED="false"

HTTP_CODE=""
CURL_RESULT=1
LISTENER_OUTPUT=""

cd "$ROOT" || {
    emit_prerequisite_failure \
      "start runtime" \
      "Unable to enter repository"

    exit 1
}

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
"$PYTHON_PATH" \
  -m uvicorn \
  "$RUNTIME_TARGET" \
  --host "$HOST" \
  --port "$PORT" \
  >"$SERVER_LOG" \
  2>&1 &

PID="$!"

for _ in {1..40}; do
    if kill -0 "$PID" >/dev/null 2>&1; then
        PROCESS_STARTED="true"
    else
        break
    fi

    HTTP_CODE="$(
        curl \
          --silent \
          --show-error \
          --max-time 2 \
          --output "$RESPONSE_FILE" \
          --write-out '%{http_code}' \
          "http://$HOST:$PORT$HEALTH_PATH" \
          2>/dev/null
    )"

    CURL_RESULT="$?"

    if [[ "$CURL_RESULT" -eq 0 ]] \
        && [[ "$HTTP_CODE" == "200" ]]
    then
        HTTP_200="true"
        break
    fi

    sleep 0.25
done

if [[ -s "$RESPONSE_FILE" ]] \
    && jq empty "$RESPONSE_FILE" >/dev/null 2>&1
then
    JSON_VALID="true"

    if jq -e \
        'type == "object"' \
        "$RESPONSE_FILE" \
        >/dev/null 2>&1
    then
        JSON_OBJECT="true"
    fi
fi

LISTENER_OUTPUT="$(
    lsof \
      -nP \
      -a \
      -p "$PID" \
      -iTCP:"$PORT" \
      -sTCP:LISTEN \
      2>/dev/null \
      || true
)"

printf '%s\n' "$LISTENER_OUTPUT" \
  > "$LISTENER_FILE"

if printf '%s\n' "$LISTENER_OUTPUT" \
    | grep -Fq "$HOST:$PORT" \
    && ! printf '%s\n' "$LISTENER_OUTPUT" \
      | grep -Eq "(\*|0\.0\.0\.0):$PORT"
then
    LISTENER_LOCAL_ONLY="true"
fi

if kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true

    for _ in {1..30}; do
        if ! kill -0 "$PID" >/dev/null 2>&1; then
            PROCESS_STOPPED="true"
            break
        fi

        sleep 0.1
    done
else
    PROCESS_STOPPED="true"
fi

wait "$PID" >/dev/null 2>&1 || true
PID=""

for _ in {1..30}; do
    if ! lsof \
        -nP \
        -iTCP:"$PORT" \
        -sTCP:LISTEN \
        >/dev/null 2>&1
    then
        PORT_RELEASED="true"
        break
    fi

    sleep 0.1
done

GATE_PASSED="false"

if [[ "$PROCESS_STARTED" == "true" ]] \
    && [[ "$HTTP_200" == "true" ]] \
    && [[ "$JSON_VALID" == "true" ]] \
    && [[ "$JSON_OBJECT" == "true" ]] \
    && [[ "$LISTENER_LOCAL_ONLY" == "true" ]] \
    && [[ "$PROCESS_STOPPED" == "true" ]] \
    && [[ "$PORT_RELEASED" == "true" ]]
then
    GATE_PASSED="true"
fi

RESPONSE_JSON="null"

if [[ "$JSON_VALID" == "true" ]]; then
    RESPONSE_JSON="$(
        cat "$RESPONSE_FILE"
    )"
fi

jq -n \
  --arg schema_version "1.0" \
  --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --arg repository "$ROOT" \
  --arg commit "$CURRENT_COMMIT" \
  --arg runtime "$CURRENT_VENV" \
  --arg runtime_target "$RUNTIME_TARGET" \
  --arg host "$HOST" \
  --argjson port "$PORT" \
  --arg health_path "$HEALTH_PATH" \
  --arg http_code "$HTTP_CODE" \
  --arg log_directory "$LOG_DIR" \
  --arg server_log "$SERVER_LOG" \
  --arg response_file "$RESPONSE_FILE" \
  --arg listener_file "$LISTENER_FILE" \
  --argjson response "$RESPONSE_JSON" \
  --argjson process_started "$PROCESS_STARTED" \
  --argjson http_200 "$HTTP_200" \
  --argjson json_valid "$JSON_VALID" \
  --argjson json_object "$JSON_OBJECT" \
  --argjson listener_local_only "$LISTENER_LOCAL_ONLY" \
  --argjson process_stopped "$PROCESS_STOPPED" \
  --argjson port_released "$PORT_RELEASED" \
  --argjson gate_passed "$GATE_PASSED" \
  '{
      schema_version: $schema_version,
      generated_at: $generated_at,
      production_health_gate_passed: $gate_passed,
      repository: {
          path: $repository,
          commit: $commit
      },
      runtime: {
          path: $runtime,
          target: $runtime_target
      },
      endpoint: {
          host: $host,
          port: $port,
          path: $health_path,
          http_code: $http_code
      },
      checks: {
          process_started: $process_started,
          http_200: $http_200,
          json_valid: $json_valid,
          json_object: $json_object,
          listener_local_only: $listener_local_only,
          process_stopped: $process_stopped,
          port_released: $port_released
      },
      response: $response,
      logs: {
          directory: $log_directory,
          server: $server_log,
          response: $response_file,
          listener: $listener_file
      },
      safety: {
          localhost_only: true,
          secret_values_read: false,
          launchd_modified: false,
          ubuntu_modified: false
      }
  }'

if [[ "$GATE_PASSED" == "true" ]]; then
    exit 0
fi

exit 1
