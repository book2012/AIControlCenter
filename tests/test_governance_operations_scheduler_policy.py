from __future__ import annotations

import plistlib
from pathlib import Path

import pytest

from core.governance.operations.scheduler_policy import (
    SchedulerPolicyError,
    load_policy,
    render_documents,
    write_documents,
)


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)
POLICY_PATH = (
    REPOSITORY_ROOT
    / "config/"
    "governance_operations_scheduler_policy.json"
)


def test_explicit_cadence_and_deployment():
    policy = load_policy(POLICY_PATH)
    definitions = {
        item["operation"]: item
        for item in policy["definitions"]
    }

    assert policy["timezone"] == "Asia/Seoul"
    assert policy["deployment"] == {
        "domain": "system",
        "home": "/Users/kyouhan",
        "install_directory": (
            "/Library/LaunchDaemons"
        ),
        "run_as_user": "kyouhan",
    }
    assert definitions[
        "governance_audit_snapshot"
    ]["calendar"] == {
        "Hour": 3,
        "Minute": 10,
    }
    assert definitions[
        "sqlite_online_backup_verification"
    ]["calendar"] == {
        "Hour": 4,
        "Minute": 10,
        "Weekday": 0,
    }


def test_policy_disables_unsafe_automation():
    policy = load_policy(POLICY_PATH)

    assert policy["safety"] == {
        "automatic_catch_up": False,
        "automatic_remediation": False,
        "automatic_restore": False,
        "automatic_retry": False,
        "disabled_by_default": True,
        "keep_alive": False,
        "run_at_load": False,
    }


def test_rendered_system_daemons_are_safe(
    tmp_path: Path,
):
    policy = load_policy(POLICY_PATH)
    rendered = render_documents(
        policy,
        repository_root=REPOSITORY_ROOT,
        python_executable=(
            REPOSITORY_ROOT
            / ".venv/bin/python"
        ),
        log_directory=tmp_path / "logs",
    )

    assert len(rendered) == 2

    for document in rendered.values():
        assert "Disabled" not in document
        assert document["UserName"] == "kyouhan"
        assert document["RunAtLoad"] is False
        assert document["KeepAlive"] is False
        assert (
            document["EnvironmentVariables"][
                "HOME"
            ]
            == "/Users/kyouhan"
        )
        assert (
            "StartCalendarInterval"
            in document
        )
        assert (
            "StartInterval"
            not in document
        )
        assert (
            "--once"
            in document["ProgramArguments"]
        )
        assert (
            "--json"
            in document["ProgramArguments"]
        )


def test_temporary_plists_parse(
    tmp_path: Path,
):
    policy = load_policy(POLICY_PATH)
    paths = write_documents(
        policy,
        output_directory=(
            tmp_path / "rendered"
        ),
        repository_root=REPOSITORY_ROOT,
        python_executable=(
            REPOSITORY_ROOT
            / ".venv/bin/python"
        ),
        log_directory=tmp_path / "logs",
    )

    assert len(paths) == 2

    for path in paths:
        document = plistlib.loads(
            path.read_bytes()
        )

        assert document["UserName"] == "kyouhan"
        assert "Disabled" not in document


def test_renderer_refuses_production_directory():
    policy = load_policy(POLICY_PATH)

    with pytest.raises(
        SchedulerPolicyError,
        match="cannot install or activate",
    ):
        write_documents(
            policy,
            output_directory=Path(
                "/Library/LaunchDaemons"
            ),
            repository_root=REPOSITORY_ROOT,
            python_executable=(
                REPOSITORY_ROOT
                / ".venv/bin/python"
            ),
            log_directory=(
                Path.home()
                / "Library/Logs/"
                "AIControlCenter/governance"
            ),
        )
