#!/bin/bash

set -u

MODE="dry-run"
APPROVAL=""
PLAN=""
SNAPSHOT=""

usage() {
  echo "Usage:"
  echo "  install-managed-ollama.sh --approval FILE --plan FILE --snapshot FILE [--dry-run]"
  echo "  install-managed-ollama.sh --approval FILE --plan FILE --snapshot FILE --apply"
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

PYTHON="${PYTHON:-python3}"

VALIDATION_OUTPUT="$(
  "$PYTHON" - "$APPROVAL" "$PLAN" "$SNAPSHOT" <<'PY'
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

approval_path = Path(sys.argv[1])
plan_path = Path(sys.argv[2])
snapshot_path = Path(sys.argv[3])

approval = json.loads(approval_path.read_text())
plan = json.loads(plan_path.read_text())
snapshot = json.loads(snapshot_path.read_text())

canonical = json.dumps(
    plan,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")

expected_hash = hashlib.sha256(canonical).hexdigest()
errors = []

if approval.get("valid") is not True:
    errors.append("approval must be valid")

if approval.get("approval_status") != "PENDING":
    errors.append("approval status must be PENDING")

if approval.get("execution_enabled") is not False:
    errors.append("approval execution must remain disabled")

if approval.get("plan_hash") != expected_hash:
    errors.append("plan hash mismatch")

if snapshot.get("read_only") is not True:
    errors.append("snapshot must be read-only")

if snapshot.get("execution_enabled") is not False:
    errors.append("snapshot execution must remain disabled")

if snapshot.get("rollback", {}).get("required") is not True:
    errors.append("rollback snapshot is required")

expires_at = approval.get("expires_at")

try:
    parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone missing")
    if parsed.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        errors.append("approval expired")
except Exception as exc:
    errors.append(f"invalid approval expiry: {exc}")

print(json.dumps({
    "valid": not errors,
    "plan_hash": expected_hash,
    "errors": errors,
}))
PY
)"

VALIDATION_CODE=$?

if [ "$VALIDATION_CODE" -ne 0 ]; then
  echo "[FAIL] Approval validation process failed"
  exit 4
fi

VALID="$(
  printf '%s' "$VALIDATION_OUTPUT" |
    "$PYTHON" -c 'import json,sys; print(str(json.load(sys.stdin)["valid"]).lower())'
)"

if [ "$VALID" != "true" ]; then
  echo "$VALIDATION_OUTPUT"
  echo "[FAIL] Installation authorization validation failed"
  exit 5
fi

echo "MODE=$MODE"
echo "APPROVAL=$APPROVAL"
echo "PLAN=$PLAN"
echo "SNAPSHOT=$SNAPSHOT"

echo
echo "=== INSTALLATION COMMAND PLAN ==="
echo "brew install ollama"
echo "install -d -o kyouhan -g staff '/Users/kyouhan/Library/Application Support/Ollama/models'"
echo "install -d -o root -g staff '/Library/Application Support/AIControlCenter'"
echo "install -m 0640 -o root -g staff ops/macos/ollama/ollama.env.example '/Library/Application Support/AIControlCenter/ollama.env'"
echo "install -m 0644 -o root -g wheel ops/macos/ollama/com.aicontrolcenter.ollama.plist '/Library/LaunchDaemons/com.aicontrolcenter.ollama.plist'"
echo "launchctl bootstrap system '/Library/LaunchDaemons/com.aicontrolcenter.ollama.plist'"
echo "launchctl enable system/com.aicontrolcenter.ollama"
echo "launchctl kickstart -k system/com.aicontrolcenter.ollama"
echo "curl http://127.0.0.1:11434/api/tags"

if [ "$MODE" = "dry-run" ]; then
  echo
  echo "[PASS] Dry-run completed; no system changes performed"
  exit 0
fi

echo
echo "[FAIL] Apply mode is intentionally disabled in PI-006-03"
exit 6
