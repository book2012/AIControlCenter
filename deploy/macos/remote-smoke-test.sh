#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd
)"

ENV_FILE="${PROJECT_ROOT}/.env.mac-production"
PYTHON="${PROJECT_ROOT}/.venv/bin/python"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: Missing ${ENV_FILE}" >&2
    exit 1
fi

if [[ ! -x "${PYTHON}" ]]; then
    echo "ERROR: Missing virtualenv Python: ${PYTHON}" >&2
    exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${DATACENTER_HOST:?DATACENTER_HOST is required}"
: "${DATACENTER_SSH_USER:?DATACENTER_SSH_USER is required}"
: "${DATACENTER_SSH_PORT:=22}"

"${PYTHON}" - <<'PY'
from __future__ import annotations

import json
import os
import sys

from core.datacenter.snapshot import DatacenterSnapshotService
from core.worker.ssh_runner import SSHRunner
from core.worker.ubuntu import UbuntuWorkerClient

host = os.environ["DATACENTER_HOST"]
user = os.environ["DATACENTER_SSH_USER"]
port = int(os.environ.get("DATACENTER_SSH_PORT", "22"))

runner = SSHRunner(
    host=host,
    user=user,
    port=port,
)

worker = UbuntuWorkerClient(
    runner=runner,
    scripts_path="/opt/aihomedatacenter/scripts",
)

checks = {}

try:
    ready = worker.ready()
    checks["ssh_and_worker_ready"] = bool(ready.get("ready"))
except Exception as error:
    ready = {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        }
    }
    checks["ssh_and_worker_ready"] = False

snapshot = DatacenterSnapshotService(worker).status()

checks["snapshot_available"] = (
    snapshot["overall_status"]
    in {"HEALTHY", "WARNING"}
)

checks["storage_integrity"] = (
    snapshot["storage"]
    .get("database", {})
    .get("integrity")
    == "ok"
)

checks["storage_schema_v3"] = (
    snapshot["database"].get("schema_version")
    == "3"
)

checks["backup_available"] = (
    snapshot["backup"].get("overall_status")
    in {"HEALTHY", "WARNING"}
)

checks["services_available"] = (
    snapshot["services"].get("overall_status")
    in {"HEALTHY", "WARNING", "STOPPED", "EMPTY"}
)

shutdown = worker.shutdown_plan()

checks["shutdown_dry_run"] = (
    shutdown.get("mode") == "dry-run"
    and shutdown.get("executed") is False
)

overall = all(checks.values())

payload = {
    "target": {
        "host": host,
        "user": user,
        "port": port,
    },
    "checks": checks,
    "worker_ready": ready,
    "snapshot": {
        "overall_status": snapshot["overall_status"],
        "unavailable_components": snapshot.get(
            "unavailable_components",
            [],
        ),
        "storage_schema": snapshot[
            "database"
        ].get("schema_version"),
        "backup_status": snapshot[
            "backup"
        ].get("overall_status"),
        "services_status": snapshot[
            "services"
        ].get("overall_status"),
    },
    "shutdown": {
        "mode": shutdown.get("mode"),
        "approved": shutdown.get("approved"),
        "executed": shutdown.get("executed"),
        "blocking_reasons": shutdown.get(
            "blocking_reasons",
            [],
        ),
    },
    "overall": "PASS" if overall else "FAIL",
}

print(
    json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )
)

raise SystemExit(0 if overall else 1)
PY
