#!/usr/bin/env bash

set -Eeuo pipefail

EXPECTED_BRANCH="${EXPECTED_BRANCH:-sprint/mac-control-plane-foundation}"
EXPECTED_TAG="${EXPECTED_TAG:-storefront-v0.16.0-rc1}"
REPO="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"

has_command() {
    command -v "$1" >/dev/null 2>&1
}

json_bool() {
    if "$@" >/dev/null 2>&1; then
        printf 'true'
    else
        printf 'false'
    fi
}

directory_mode() {
    local path="$1"

    if [[ ! -d "$path" ]]; then
        printf ''
        return
    fi

    stat -f '%Lp' "$path" 2>/dev/null || true
}

DARWIN="$(
    json_bool test "$(uname -s 2>/dev/null || true)" = "Darwin"
)"

APPLE_SILICON="$(
    json_bool test "$(uname -m 2>/dev/null || true)" = "arm64"
)"

XCODE_PATH="$(
    xcode-select -p 2>/dev/null || true
)"

XCODE_READY="$(
    json_bool test -n "$XCODE_PATH"
)"

BREW_READY="$(
    json_bool has_command brew
)"

GIT_READY="$(
    json_bool has_command git
)"

GH_READY="$(
    json_bool has_command gh
)"

JQ_READY="$(
    json_bool has_command jq
)"

PYTHON_READY="$(
    json_bool has_command python3.12
)"

GH_AUTHENTICATED="false"
GH_PROTOCOL=""
GH_ACCOUNT=""

if has_command gh; then
    GH_AUTHENTICATED="$(
        json_bool gh auth status --hostname github.com
    )"

    GH_PROTOCOL="$(
        gh config get \
          git_protocol \
          --host github.com \
          2>/dev/null \
          || true
    )"

    if [[ "$GH_AUTHENTICATED" == "true" ]]; then
        GH_ACCOUNT="$(
            gh api user \
              --jq '.login' \
              2>/dev/null \
              || true
        )"
    fi
fi

GH_SSH_PROTOCOL="$(
    json_bool test "$GH_PROTOCOL" = "ssh"
)"

FILEVAULT_RAW="$(
    fdesetup status 2>/dev/null || true
)"

FILEVAULT_ENABLED="false"

if [[ "$FILEVAULT_RAW" == *"FileVault is On"* ]]; then
    FILEVAULT_ENABLED="true"
fi

FIREWALL_RAW="$(
    /usr/libexec/ApplicationFirewall/socketfilterfw \
      --getglobalstate \
      2>/dev/null \
      || true
)"

FIREWALL_ENABLED="false"

if [[ "$FIREWALL_RAW" == *"enabled"* ]] \
    || [[ "$FIREWALL_RAW" == *"State = 1"* ]]
then
    FIREWALL_ENABLED="true"
fi

STEALTH_RAW="$(
    /usr/libexec/ApplicationFirewall/socketfilterfw \
      --getstealthmode \
      2>/dev/null \
      || true
)"

STEALTH_ENABLED="false"

if [[ "$STEALTH_RAW" == *"enabled"* ]] \
    || [[ "$STEALTH_RAW" == *"enabled = 1"* ]]
then
    STEALTH_ENABLED="true"
fi

REPO_EXISTS="false"
REPO_BRANCH=""
REPO_COMMIT=""
REPO_REMOTE=""
REPO_CLEAN="false"
EXPECTED_TAG_VISIBLE="false"
EXPECTED_BRANCH_ACTIVE="false"

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

    REPO_REMOTE="$(
        git -C "$REPO" \
          remote get-url origin \
          2>/dev/null \
          || true
    )"

    if [[ -z "$(
        git -C "$REPO" \
          status --porcelain \
          2>/dev/null
    )" ]]; then
        REPO_CLEAN="true"
    fi

    if git -C "$REPO" \
        rev-parse \
        "$EXPECTED_TAG" \
        >/dev/null 2>&1
    then
        EXPECTED_TAG_VISIBLE="true"
    fi

    if [[ "$REPO_BRANCH" == "$EXPECTED_BRANCH" ]]; then
        EXPECTED_BRANCH_ACTIVE="true"
    fi
fi

CONFIG_DIR="$HOME/.config/aicontrolcenter"
SECRETS_DIR="$CONFIG_DIR/secrets"
RUNTIME_DIR="$CONFIG_DIR/runtime"
LOG_DIR="$HOME/Library/Logs/AIControlCenter"
DATA_DIR="$HOME/Library/Application Support/AIControlCenter"

CONFIG_MODE="$(
    directory_mode "$CONFIG_DIR"
)"

SECRETS_MODE="$(
    directory_mode "$SECRETS_DIR"
)"

RUNTIME_MODE="$(
    directory_mode "$RUNTIME_DIR"
)"

CONFIG_DIR_READY="false"
SECRETS_DIR_READY="false"
RUNTIME_DIR_READY="false"
LOG_DIR_READY="false"
DATA_DIR_READY="false"

if [[ -d "$CONFIG_DIR" && "$CONFIG_MODE" == "700" ]]; then
    CONFIG_DIR_READY="true"
fi

if [[ -d "$SECRETS_DIR" && "$SECRETS_MODE" == "700" ]]; then
    SECRETS_DIR_READY="true"
fi

if [[ -d "$RUNTIME_DIR" && "$RUNTIME_MODE" == "700" ]]; then
    RUNTIME_DIR_READY="true"
fi

if [[ -d "$LOG_DIR" ]]; then
    LOG_DIR_READY="true"
fi

if [[ -d "$DATA_DIR" ]]; then
    DATA_DIR_READY="true"
fi

PRODUCTION_GATE_PASSED="true"

REQUIRED_CHECKS=(
    "$DARWIN"
    "$APPLE_SILICON"
    "$XCODE_READY"
    "$BREW_READY"
    "$GIT_READY"
    "$GH_READY"
    "$JQ_READY"
    "$PYTHON_READY"
    "$GH_AUTHENTICATED"
    "$GH_SSH_PROTOCOL"
    "$FILEVAULT_ENABLED"
    "$FIREWALL_ENABLED"
    "$STEALTH_ENABLED"
    "$REPO_EXISTS"
    "$REPO_CLEAN"
    "$EXPECTED_TAG_VISIBLE"
    "$EXPECTED_BRANCH_ACTIVE"
    "$CONFIG_DIR_READY"
    "$SECRETS_DIR_READY"
    "$RUNTIME_DIR_READY"
    "$LOG_DIR_READY"
    "$DATA_DIR_READY"
)

for check in "${REQUIRED_CHECKS[@]}"; do
    if [[ "$check" != "true" ]]; then
        PRODUCTION_GATE_PASSED="false"
        break
    fi
done

jq -n \
  --arg schema_version "1.0" \
  --arg generated_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --arg expected_branch "$EXPECTED_BRANCH" \
  --arg expected_tag "$EXPECTED_TAG" \
  --arg repo_path "$REPO" \
  --arg repo_branch "$REPO_BRANCH" \
  --arg repo_commit "$REPO_COMMIT" \
  --arg repo_remote "$REPO_REMOTE" \
  --arg gh_account "$GH_ACCOUNT" \
  --arg gh_protocol "$GH_PROTOCOL" \
  --arg filevault_raw "$FILEVAULT_RAW" \
  --arg firewall_raw "$FIREWALL_RAW" \
  --arg stealth_raw "$STEALTH_RAW" \
  --arg xcode_path "$XCODE_PATH" \
  --arg config_mode "$CONFIG_MODE" \
  --arg secrets_mode "$SECRETS_MODE" \
  --arg runtime_mode "$RUNTIME_MODE" \
  --argjson darwin "$DARWIN" \
  --argjson apple_silicon "$APPLE_SILICON" \
  --argjson xcode_ready "$XCODE_READY" \
  --argjson homebrew_ready "$BREW_READY" \
  --argjson git_ready "$GIT_READY" \
  --argjson github_cli_ready "$GH_READY" \
  --argjson jq_ready "$JQ_READY" \
  --argjson python_312_ready "$PYTHON_READY" \
  --argjson github_authenticated "$GH_AUTHENTICATED" \
  --argjson github_ssh_protocol "$GH_SSH_PROTOCOL" \
  --argjson filevault_enabled "$FILEVAULT_ENABLED" \
  --argjson firewall_enabled "$FIREWALL_ENABLED" \
  --argjson stealth_mode_enabled "$STEALTH_ENABLED" \
  --argjson repository_exists "$REPO_EXISTS" \
  --argjson repository_clean "$REPO_CLEAN" \
  --argjson expected_tag_visible "$EXPECTED_TAG_VISIBLE" \
  --argjson expected_branch_active "$EXPECTED_BRANCH_ACTIVE" \
  --argjson config_directory_ready "$CONFIG_DIR_READY" \
  --argjson secrets_directory_ready "$SECRETS_DIR_READY" \
  --argjson runtime_directory_ready "$RUNTIME_DIR_READY" \
  --argjson log_directory_ready "$LOG_DIR_READY" \
  --argjson data_directory_ready "$DATA_DIR_READY" \
  --argjson production_gate_passed "$PRODUCTION_GATE_PASSED" \
  '{
      schema_version: $schema_version,
      generated_at: $generated_at,
      production_gate_passed: $production_gate_passed,
      expectations: {
          branch: $expected_branch,
          release_candidate_tag: $expected_tag
      },
      checks: {
          macos: $darwin,
          apple_silicon: $apple_silicon,
          xcode_command_line_tools: $xcode_ready,
          homebrew: $homebrew_ready,
          git: $git_ready,
          github_cli: $github_cli_ready,
          jq: $jq_ready,
          python_3_12: $python_312_ready,
          github_authenticated: $github_authenticated,
          github_git_protocol_ssh: $github_ssh_protocol,
          filevault: $filevault_enabled,
          firewall: $firewall_enabled,
          stealth_mode: $stealth_mode_enabled,
          repository_exists: $repository_exists,
          repository_clean: $repository_clean,
          expected_tag_visible: $expected_tag_visible,
          expected_branch_active: $expected_branch_active,
          config_directory_mode_700: $config_directory_ready,
          secrets_directory_mode_700: $secrets_directory_ready,
          runtime_directory_mode_700: $runtime_directory_ready,
          log_directory_exists: $log_directory_ready,
          data_directory_exists: $data_directory_ready
      },
      details: {
          github: {
              account: $gh_account,
              git_protocol: $gh_protocol
          },
          security: {
              filevault: $filevault_raw,
              firewall: $firewall_raw,
              stealth_mode: $stealth_raw
          },
          developer_tools: {
              xcode_path: $xcode_path
          },
          repository: {
              path: $repo_path,
              branch: $repo_branch,
              commit: $repo_commit,
              remote: $repo_remote
          },
          directory_modes: {
              config: $config_mode,
              secrets: $secrets_mode,
              runtime: $runtime_mode
          }
      }
  }'
