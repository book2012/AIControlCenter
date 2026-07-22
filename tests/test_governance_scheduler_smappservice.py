from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "config/"
    "governance_scheduler_smappservice.json"
)
BUILDER_PATH = (
    REPOSITORY_ROOT
    / "scripts/"
    "build_governance_scheduler_smappservice.py"
)

SPEC = importlib.util.spec_from_file_location(
    "governance_scheduler_smappservice_builder",
    BUILDER_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None

BUILDER = importlib.util.module_from_spec(
    SPEC
)
SPEC.loader.exec_module(BUILDER)


def test_adapter_configuration():
    config = json.loads(
        CONFIG_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert config["owner"] == "AIControlCenter"
    assert (
        config["deployment_method"]
        == "SMAppService"
    )
    assert (
        config[
            "direct_launchctl_installation"
        ]
        is False
    )
    assert (
        config["user_approval_required"]
        is True
    )


def test_builder_uses_explicit_macos_sdk():
    source = BUILDER_PATH.read_text(
        encoding="utf-8"
    )

    assert "--show-sdk-path" in source
    assert '"-sdk"' in source
    assert '"swiftc"' in source
    assert '"-target"' in source


def test_agent_document_is_bundle_relative(
    tmp_path: Path,
):
    document = (
        BUILDER.build_agent_document(
            definition={
                "calendar": {
                    "Hour": 3,
                    "Minute": 10,
                },
                "label": (
                    "com.aicontrolcenter.test"
                ),
                "operation": (
                    "governance_audit_snapshot"
                ),
            },
            repository_root=(
                REPOSITORY_ROOT
            ),
            runner_executable=(
                "AIControlCenterGovernanceRunner"
            ),
            log_directory=tmp_path,
        )
    )

    assert document["BundleProgram"] == (
        "Contents/Resources/"
        "AIControlCenterGovernanceRunner"
    )
    assert "Program" not in document
    assert "UserName" not in document
    assert "Disabled" not in document
    assert (
        "AssociatedBundleIdentifiers"
        not in document
    )
    assert document["RunAtLoad"] is False
    assert document["KeepAlive"] is False


def test_agent_document_has_explicit_cadence(
    tmp_path: Path,
):
    document = (
        BUILDER.build_agent_document(
            definition={
                "calendar": {
                    "Hour": 4,
                    "Minute": 10,
                    "Weekday": 0,
                },
                "label": (
                    "com.aicontrolcenter.test"
                ),
                "operation": (
                    "sqlite_online_backup_verification"
                ),
            },
            repository_root=(
                REPOSITORY_ROOT
            ),
            runner_executable=(
                "AIControlCenterGovernanceRunner"
            ),
            log_directory=tmp_path,
        )
    )

    assert document[
        "StartCalendarInterval"
    ] == {
        "Hour": 4,
        "Minute": 10,
        "Weekday": 0,
    }


def test_registrar_uses_smappservice_only():
    source = (
        REPOSITORY_ROOT
        / "macos/governance_scheduler/"
        "Registrar.swift"
    ).read_text(encoding="utf-8")

    assert "SMAppService.agent" in source
    assert "register()" in source
    assert "unregister" in source
    assert "launchctl" not in source


def test_runner_is_one_shot_json():
    source = (
        REPOSITORY_ROOT
        / "macos/governance_scheduler/"
        "Runner.swift"
    ).read_text(encoding="utf-8")

    assert "--once" in source
    assert "--json" in source
    assert "automatic_retry" in source
