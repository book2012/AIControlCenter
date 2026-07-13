#!/usr/bin/env bash

set -Eeuo pipefail

REPO="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"

has_command() {
    command -v "$1" >/dev/null 2>&1
}

command_version() {
    local command_name="$1"

    if ! has_command "$command_name"; then
        printf '%s' ""
        return
    fi

    "$command_name" --version 2>&1 \
        | head -n 1 \
        | tr -d '\r'
}

MACOS_VERSION="$(
    sw_vers -productVersion 2>/dev/null || true
)"

MACOS_BUILD="$(
    sw_vers -buildVersion 2>/dev/null || true
)"

ARCHITECTURE="$(
    uname -m 2>/dev/null || true
)"

COMPUTER_NAME="$(
    scutil --get ComputerName 2>/dev/null || true
)"

LOCAL_HOST_NAME="$(
    scutil --get LocalHostName 2>/dev/null || true
)"

FILEVAULT_STATUS="$(
    fdesetup status 2>/dev/null || true
)"

FIREWALL_STATUS="$(
    /usr/libexec/ApplicationFirewall/socketfilterfw \
        --getglobalstate \
        2>/dev/null \
        || true
)"

STEALTH_STATUS="$(
    /usr/libexec/ApplicationFirewall/socketfilterfw \
        --getstealthmode \
        2>/dev/null \
        || true
)"

DISK_FREE_BYTES="$(
    df -k / \
        | awk 'NR == 2 {print $4 * 1024}'
)"

MEMORY_BYTES="$(
    sysctl -n hw.memsize 2>/dev/null || echo 0
)"

REPO_EXISTS="false"
REPO_BRANCH=""
REPO_COMMIT=""
REPO_DIRTY_COUNT=0
RC_TAG_VISIBLE="false"

if [[ -d "$REPO/.git" ]]; then
    REPO_EXISTS="true"

    REPO_BRANCH="$(
        git -C "$REPO" \
            branch --show-current \
            2>/dev/null \
            || true
    )"

    REPO_COMMIT="$(
        git -C "$REPO" \
            rev-parse HEAD \
            2>/dev/null \
            || true
    )"

    REPO_DIRTY_COUNT="$(
        git -C "$REPO" \
            status --porcelain \
            2>/dev/null \
            | wc -l \
            | tr -d ' '
    )"

    if git -C "$REPO" \
        rev-parse \
        storefront-v0.16.0-rc1 \
        >/dev/null 2>&1
    then
        RC_TAG_VISIBLE="true"
    fi
fi

jq -n \
    --arg schema_version "1.0" \
    --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    --arg macos_version "$MACOS_VERSION" \
    --arg macos_build "$MACOS_BUILD" \
    --arg architecture "$ARCHITECTURE" \
    --arg computer_name "$COMPUTER_NAME" \
    --arg local_host_name "$LOCAL_HOST_NAME" \
    --arg filevault "$FILEVAULT_STATUS" \
    --arg firewall "$FIREWALL_STATUS" \
    --arg stealth_mode "$STEALTH_STATUS" \
    --arg user "$(id -un)" \
    --arg home "$HOME" \
    --arg git_version "$(command_version git)" \
    --arg gh_version "$(command_version gh)" \
    --arg brew_version "$(command_version brew)" \
    --arg python_version "$(command_version python3)" \
    --arg jq_version "$(command_version jq)" \
    --arg repo_path "$REPO" \
    --arg repo_branch "$REPO_BRANCH" \
    --arg repo_commit "$REPO_COMMIT" \
    --argjson disk_free_bytes "${DISK_FREE_BYTES:-0}" \
    --argjson memory_bytes "${MEMORY_BYTES:-0}" \
    --argjson repo_exists "$REPO_EXISTS" \
    --argjson repo_dirty_count "${REPO_DIRTY_COUNT:-0}" \
    --argjson rc_tag_visible "$RC_TAG_VISIBLE" \
    '{
        schema_version: $schema_version,
        generated_at: $generated_at,
        system: {
            macos_version: $macos_version,
            macos_build: $macos_build,
            architecture: $architecture,
            computer_name: $computer_name,
            local_host_name: $local_host_name,
            user: $user,
            home: $home,
            memory_bytes: $memory_bytes,
            root_disk_free_bytes: $disk_free_bytes
        },
        security: {
            filevault: $filevault,
            firewall: $firewall,
            stealth_mode: $stealth_mode
        },
        tools: {
            git: $git_version,
            github_cli: $gh_version,
            homebrew: $brew_version,
            python: $python_version,
            jq: $jq_version
        },
        repository: {
            path: $repo_path,
            exists: $repo_exists,
            branch: $repo_branch,
            commit: $repo_commit,
            dirty_file_count: $repo_dirty_count,
            storefront_rc_tag_visible: $rc_tag_visible
        }
    }'
