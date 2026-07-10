#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/AIControlCenter}"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$LAUNCH_AGENTS"

for template in deploy/launchd/*.plist.template; do
    name="$(basename "$template" .template)"

    sed \
        "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" \
        "$template" > "$LAUNCH_AGENTS/$name"

    plutil -lint "$LAUNCH_AGENTS/$name"
done

echo "launchd files installed in:"
echo "$LAUNCH_AGENTS"
