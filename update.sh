#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/AIControlCenter}"
BRANCH="${BRANCH:-main}"

cd "$PROJECT_ROOT"

echo "== AIControlCenter Update =="

if [[ ! -d .git ]]; then
    echo "ERROR: Git repository not found: $PROJECT_ROOT"
    exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: Uncommitted changes detected."
    git status --short
    exit 1
fi

echo "[1/6] Fetching repository..."
git fetch origin

echo "[2/6] Updating branch: $BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "[3/6] Activating virtual environment..."
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "[4/6] Installing dependencies..."
python -m pip install --upgrade pip

if [[ ! -f requirements.txt ]]; then
    echo "ERROR: requirements.txt not found"
    exit 1
fi

python -m pip install -r requirements.txt

echo "[5/6] Running tests..."
pytest -q

echo "[6/6] Restarting services..."
sudo systemctl daemon-reload
sudo systemctl restart \
    aicontrolcenter-api \
    aicontrolcenter-telegram \
    aicontrolcenter-scheduler

sleep 2

for service in \
    aicontrolcenter-api \
    aicontrolcenter-telegram \
    aicontrolcenter-scheduler
do
    if ! systemctl is-active --quiet "$service"; then
        echo "ERROR: $service failed to start"
        systemctl --no-pager --full status "$service" || true
        exit 1
    fi
done

curl --fail --silent http://localhost:8000/health
echo
echo "Update completed successfully."
