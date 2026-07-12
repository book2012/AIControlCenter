#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="${AICC_PROJECT_ROOT:-/opt/AIControlCenter}"
ERRORS=0

check_file() {
    local path="$1"

    if [[ -f "${path}" ]]; then
        echo "OK   ${path}"
    else
        echo "FAIL ${path}"
        ERRORS=$((ERRORS + 1))
    fi
}

check_file "${PROJECT_ROOT}/deploy/macos/com.aihome.aicontrolcenter.plist"
check_file "${PROJECT_ROOT}/deploy/macos/install-launchd.sh"
check_file "${PROJECT_ROOT}/deploy/macos/uninstall-launchd.sh"
check_file "${PROJECT_ROOT}/config/workers.mac-production.yaml"
check_file "${PROJECT_ROOT}/.env.mac-production.example"

if [[ "$(uname -s)" == "Darwin" ]]; then
    plutil -lint \
      "${PROJECT_ROOT}/deploy/macos/com.aihome.aicontrolcenter.plist"
else
    echo "SKIP plist runtime validation: not running on macOS"
fi

if [[ "${ERRORS}" -ne 0 ]]; then
    echo "Profile validation failed."
    exit 1
fi

echo "Mac production profile validation passed."
