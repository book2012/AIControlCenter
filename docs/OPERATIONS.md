# Operations

## Services

aicontrolcenter-api

aicontrolcenter-telegram

aicontrolcenter-scheduler

## Start

sudo systemctl start aicontrolcenter-api
sudo systemctl start aicontrolcenter-telegram
sudo systemctl start aicontrolcenter-scheduler

## Stop

sudo systemctl stop aicontrolcenter-api
sudo systemctl stop aicontrolcenter-telegram
sudo systemctl stop aicontrolcenter-scheduler

## Restart

sudo systemctl restart aicontrolcenter-api
sudo systemctl restart aicontrolcenter-telegram
sudo systemctl restart aicontrolcenter-scheduler

## Logs

journalctl -u aicontrolcenter-api -f

journalctl -u aicontrolcenter-telegram -f

journalctl -u aicontrolcenter-scheduler -f

## Health

curl http://localhost:8000/health

curl http://localhost:8000/runtime/health

curl http://localhost:8000/homepage/status
