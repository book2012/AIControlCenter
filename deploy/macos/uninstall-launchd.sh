#!/usr/bin/env bash

set -Eeuo pipefail

TARGET_PLIST="${HOME}/Library/LaunchAgents/com.aihome.aicontrolcenter.plist"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: This uninstaller must run on macOS." >&2
    exit 1
fi

launchctl bootout \
  "gui/${UID}" \
  "${TARGET_PLIST}" \
  2>/dev/null || true

rm -f "${TARGET_PLIST}"

echo "AIControlCenter LaunchAgent removed."
