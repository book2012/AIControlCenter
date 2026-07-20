#!/bin/bash

set -u

MODE="dry-run"
APPROVAL=""
PLAN=""
SNAPSHOT=""
EXECUTION_TOKEN=""
BACKUP_ROOT=""

BREW_COMMAND="${BREW_COMMAND:-brew}"
INSTALL_COMMAND="${INSTALL_COMMAND:-install}"
LAUNCHCTL_COMMAND="${LAUNCHCTL_COMMAND:-launchctl}"
CURL_COMMAND="${CURL_COMMAND:-curl}"
PYTHON="${PYTHON:-python3}"
EXECUTION_GATE_MODULE="${EXECUTION_GATE_MODULE:-core.deployment.execution_gate}"
BACKUP_GENERATOR="${BACKUP_GENERATOR:-ops/macos/ollama/generate-rollback-backup.py}"

PLIST_SOURCE="ops/macos/ollama/com.aicontrolcenter.ollama.plist"
ENV_SOURCE="ops/macos/ollama/ollama.env.example"
PLIST_TARGET="${PLIST_TARGET:-/Library/LaunchDaemons/com.aicontrolcenter.ollama.plist}"
ENV_TARGET="${ENV_TARGET:-/Library/Application Support/AIControlCenter/ollama.env}"
MODELS_TARGET="${MODELS_TARGET:-/Users/kyouhan/Library/Application Support/Ollama/models}"
LOG_TARGET="${LOG_TARGET:-/Users/kyouhan/Library/Logs/AIControlCenter}"
SERVICE="${SERVICE:-system/com.aicontrolcenter.ollama}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:11434/api/tags}"

usage() {
  echo "Usage:"
  echo "  install-managed-ollama.sh --approval FILE --plan FILE --snapshot FILE [--dry-run]"
  echo "  install-managed-ollama.sh --approval FILE --plan FILE --snapshot FILE --execution-token TOKEN --backup-root DIR --apply"
}

while [ "$#" -gt 0 ]
do
  case "$1" in
    --approval)
      APPROVAL="$2"
      shift 2
      ;;
    --plan)
      PLAN="$2"
      shift 2
      ;;
    --snapshot)
      SNAPSHOT="$2"
      shift 2
      ;;
    --execution-token)
      EXECUTION_TOKEN="$2"
      shift 2
      ;;
    --backup-root)
      BACKUP_ROOT="$2"
      shift 2
      ;;
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --apply)
      MODE="apply"
      shift
      ;;
    *)
      echo "[FAIL] Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

if [ -z "$APPROVAL" ] || [ -z "$PLAN" ] || [ -z "$SNAPSHOT" ]; then
  echo "[FAIL] approval, plan and snapshot are required"
  usage
  exit 2
fi

for FILE in "$APPROVAL" "$PLAN" "$SNAPSHOT"
do
  if [ ! -f "$FILE" ]; then
    echo "[FAIL] Required file missing: $FILE"
    exit 3
  fi
done

validate_gate() {
  "$PYTHON" -m "$EXECUTION_GATE_MODULE" \
    "$APPROVAL" \
    "$PLAN" \
    "$SNAPSHOT" \
    --execution-token "$EXECUTION_TOKEN"
}

rollback() {
  ROLLBACK_DIRECTORY="$1"

  echo "[INFO] Starting automatic rollback"

  "$LAUNCHCTL_COMMAND" bootout "$SERVICE" >/dev/null 2>&1 || true

  if [ -f "$ROLLBACK_DIRECTORY/launchd/com.aicontrolcenter.ollama.plist" ]; then
    "$INSTALL_COMMAND" -m 0644 \
      "$ROLLBACK_DIRECTORY/launchd/com.aicontrolcenter.ollama.plist" \
      "$PLIST_TARGET" || true
  else
    rm -f "$PLIST_TARGET"
  fi

  if [ -f "$ROLLBACK_DIRECTORY/environment/ollama.env" ]; then
    "$INSTALL_COMMAND" -m 0640 \
      "$ROLLBACK_DIRECTORY/environment/ollama.env" \
      "$ENV_TARGET" || true
  else
    rm -f "$ENV_TARGET"
  fi

  if [ -f "$ROLLBACK_DIRECTORY/binary/ollama" ]; then
    "$INSTALL_COMMAND" -m 0755 \
      "$ROLLBACK_DIRECTORY/binary/ollama" \
      /opt/homebrew/bin/ollama || true
  fi

  echo "[PASS] Automatic rollback completed"
}

echo "MODE=$MODE"
echo "APPROVAL=$APPROVAL"
echo "PLAN=$PLAN"
echo "SNAPSHOT=$SNAPSHOT"

if [ "$MODE" = "dry-run" ]; then
  echo "brew install ollama"
  echo "create rollback backup"
  echo "install environment contract"
  echo "install LaunchDaemon"
  echo "bootstrap $SERVICE"
  echo "validate $HEALTH_URL"
  echo "[PASS] Dry-run completed; no system changes performed"
  exit 0
fi

if [ -z "$EXECUTION_TOKEN" ]; then
  echo "[FAIL] execution token is required for apply mode"
  exit 4
fi

if [ -z "$BACKUP_ROOT" ]; then
  echo "[FAIL] backup root is required for apply mode"
  exit 4
fi

GATE_OUTPUT="/tmp/pi006-ollama-execution-gate.json"

validate_gate > "$GATE_OUTPUT"
GATE_CODE=$?

if [ "$GATE_CODE" -ne 0 ]; then
  cat "$GATE_OUTPUT"
  echo "[FAIL] Execution gate blocked apply mode"
  exit 5
fi

GATE_STATUS="$(jq -r ".gate_status" "$GATE_OUTPUT")"

if [ "$GATE_STATUS" != "AUTHORIZED" ]; then
  echo "[FAIL] Execution gate is not AUTHORIZED"
  exit 5
fi

BACKUP_RESULT="/tmp/pi006-ollama-apply-backup.json"

"$PYTHON" "$BACKUP_GENERATOR" \
  --output-root "$BACKUP_ROOT" \
  --write-backup \
  > "$BACKUP_RESULT"

BACKUP_CODE=$?

if [ "$BACKUP_CODE" -ne 0 ]; then
  echo "[FAIL] Rollback backup generation failed"
  exit 6
fi

BACKUP_DIRECTORY="$(jq -r ".backup_directory" "$BACKUP_RESULT")"
MANIFEST_PATH="$(jq -r ".manifest_path" "$BACKUP_RESULT")"

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "[FAIL] Rollback backup manifest missing"
  exit 6
fi

APPLY_CODE=0

"$BREW_COMMAND" install ollama || APPLY_CODE=1

if [ "$APPLY_CODE" -eq 0 ]; then
  "$INSTALL_COMMAND" -d "$MODELS_TARGET" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$INSTALL_COMMAND" -d "$LOG_TARGET" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$INSTALL_COMMAND" -d "/Library/Application Support/AIControlCenter" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$INSTALL_COMMAND" -m 0640 "$ENV_SOURCE" "$ENV_TARGET" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$INSTALL_COMMAND" -m 0644 "$PLIST_SOURCE" "$PLIST_TARGET" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$LAUNCHCTL_COMMAND" bootout "$SERVICE" >/dev/null 2>&1 || true
  "$LAUNCHCTL_COMMAND" bootstrap system "$PLIST_TARGET" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$LAUNCHCTL_COMMAND" enable "$SERVICE" || APPLY_CODE=1
fi

if [ "$APPLY_CODE" -eq 0 ]; then
  "$LAUNCHCTL_COMMAND" kickstart -k "$SERVICE" || APPLY_CODE=1
fi

HEALTH_CODE=1

if [ "$APPLY_CODE" -eq 0 ]; then
  for attempt in 1 2 3 4 5 6 7 8 9 10
  do
    "$CURL_COMMAND" -fsS --max-time 5 "$HEALTH_URL" >/dev/null 2>&1
    HEALTH_CODE=$?

    if [ "$HEALTH_CODE" -eq 0 ]; then
      break
    fi

    sleep 1
  done
fi

if [ "$APPLY_CODE" -ne 0 ] || [ "$HEALTH_CODE" -ne 0 ]; then
  echo "[FAIL] Ollama apply or health validation failed"
  rollback "$BACKUP_DIRECTORY"
  exit 7
fi

echo "BACKUP_DIRECTORY=$BACKUP_DIRECTORY"
echo "BACKUP_MANIFEST=$MANIFEST_PATH"
echo "[PASS] Ollama managed installation applied successfully"
exit 0
