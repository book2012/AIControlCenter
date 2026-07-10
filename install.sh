#!/usr/bin/env bash
set -e

PROJECT=/opt/AIControlCenter

cd "$PROJECT"

echo "== AIControlCenter Installation =="

python3 -m venv .venv || true

source .venv/bin/activate

pip install --upgrade pip

if [ -f requirements.txt ]; then
    python -m pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found"
    exit 1
fi

mkdir -p logs

if [ ! -f .env ]; then
    cp .env.example .env
fi

sudo cp deploy/systemd/*.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable aicontrolcenter-api
sudo systemctl enable aicontrolcenter-telegram
sudo systemctl enable aicontrolcenter-scheduler

echo
echo "Installation completed."
echo
echo "Start services with:"
echo "sudo systemctl start aicontrolcenter-api"
echo "sudo systemctl start aicontrolcenter-telegram"
echo "sudo systemctl start aicontrolcenter-scheduler"
