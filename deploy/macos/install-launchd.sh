#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="${AICC_PROJECT_ROOT:-/opt/AIControlCenter}"
SOURCE_PLIST="${PROJECT_ROOT}/deploy/macos/com.aihome.aicontrolcenter.plist"
TARGET_PLIST="${HOME}/Library/LaunchAgents/com.aihome.aicontrolcenter.plist"
LOG_DIR="${PROJECT_ROOT}/var/log"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: This installer must run on macOS." >&2
    exit 1
fi

if [[ ! -f "${SOURCE_PLIST}" ]]; then
    echo "ERROR: Missing plist: ${SOURCE_PLIST}" >&2
    exit 1
fi

if [[ ! -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    echo "ERROR: Missing virtualenv Python." >&2
    exit 1
fi

mkdir -p "${HOME}/Library/LaunchAgents"
mkdir -p "${LOG_DIR}"

plutil -lint "${SOURCE_PLIST}"
cp "${SOURCE_PLIST}" "${TARGET_PLIST}"

launchctl bootout \
  "gui/${UID}" \
  "${TARGET_PLIST}" \
  2>/dev/null || true

launchctl bootstrap \
  "gui/${UID}" \
  "${TARGET_PLIST}"

launchctl enable \
  "gui/${UID}/com.aihome.aicontrolcenter"

echo "Installed: ${TARGET_PLIST}"
echo "Check:"
echo "launchctl print gui/${UID}/com.aihome.aicontrolcenter"
