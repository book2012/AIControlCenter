from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from core.governance.operations.scheduler import (
    build_service,
    composition_descriptor,
    execute_once,
    load_config,
    validate_composition_symbols,
)


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "config/"
    "governance_operations_runner.json"
)


class FakeService:
    def __init__(self) -> None:
        self.command = None

    def dispatch(self, command):
        self.command = command
        return {
            "state": "succeeded",
        }


def test_runner_policy_disables_scheduling():
    document = load_config(CONFIG_PATH)

    assert document["safety"] == {
        "automatic_catch_up": False,
        "automatic_remediation": False,
        "automatic_restore": False,
        "automatic_retry": False,
        "launchd_activation_enabled": False,
        "scheduling_enabled": False,
    }


def test_composition_symbols_import():
    validate_composition_symbols(
        CONFIG_PATH
    )

    assert set(
        composition_descriptor(
            CONFIG_PATH
        )
    ) == {
        "repository",
        "clock",
        "snapshot_executor",
        "backup_verifier",
    }


def test_build_service_uses_ephemeral_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    database = (
        tmp_path
        / "data/audit.sqlite3"
    )
    database.parent.mkdir(
        parents=True
    )

    with sqlite3.connect(database):
        pass

    monkeypatch.setenv(
        "AICONTROLCENTER_GOVERNANCE_AUDIT_DB",
        str(database),
    )

    service = build_service(
        CONFIG_PATH
    )

    assert callable(service.dispatch)


@pytest.mark.parametrize(
    "operation",
    [
        "governance_audit_snapshot",
        (
            "sqlite_online_backup_"
            "verification"
        ),
    ],
)
def test_execute_once_builds_command(
    tmp_path: Path,
    operation: str,
):
    service = FakeService()
    scheduled_for = datetime(
        2026,
        7,
        22,
        tzinfo=timezone.utc,
    )
    dispatch_id = UUID(
        "00000000-0000-0000-0000-"
        "000000000009"
    )

    result = execute_once(
        operation,
        config_path=CONFIG_PATH,
        lock_directory=(
            tmp_path / "locks"
        ),
        service_override=service,
        scheduled_for=scheduled_for,
        dispatch_id=dispatch_id,
    )

    assert result["result"] == "PASS"
    assert (
        result["automatic_retry"]
        is False
    )
    assert result["operation"] == operation
    assert service.command is not None
    assert (
        service.command.operation.value
        == operation
    )
    assert (
        service.command.scheduled_for
        == scheduled_for
    )
    assert (
        service.command.dispatch_id
        == dispatch_id
    )
    assert service.command.attempt == 1
    json.dumps(result)
