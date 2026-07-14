from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]

MODULE_PATH = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "canonical_shadow_daemon.py"
)


def load_module() -> ModuleType:
    specification = (
        importlib.util.spec_from_file_location(
            "canonical_shadow_daemon",
            MODULE_PATH,
        )
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(
        specification
    )

    specification.loader.exec_module(
        module
    )

    return module


def test_module_exists() -> None:
    assert MODULE_PATH.is_file()


def test_canonical_contract_passes() -> None:
    module = load_module()

    result = module.validate_contract(
        ROOT
    )

    assert result[
        "canonical_launchd_contract_gate_passed"
    ] is True

    assert all(
        result["checks"].values()
    )


def test_install_plan_is_json_serializable() -> None:
    module = load_module()

    plan = module.build_install_plan(
        ROOT
    )

    json.dumps(plan)


def test_install_plan_is_dry_run() -> None:
    module = load_module()

    plan = module.build_install_plan(
        ROOT
    )

    assert plan[
        "write_operations_executed"
    ] is False


def test_install_plan_uses_canonical_assets() -> None:
    module = load_module()

    plan = module.build_install_plan(
        ROOT
    )

    install_steps = [
        step
        for step in plan[
            "installation_plan"
        ]
        if step["step"] == "install_file"
    ]

    sources = {
        step["source"]
        for step in install_steps
    }

    assert str(
        ROOT
        / "ops"
        / "macos"
        / "launchd"
        / "com.aicontrolcenter.api.shadow.plist"
    ) in sources

    assert str(
        ROOT
        / "ops"
        / "macos"
        / "launchd"
        / "run-shadow-daemon.sh"
    ) in sources


def test_install_plan_security_contract() -> None:
    module = load_module()

    plan = module.build_install_plan(
        ROOT
    )

    installation = plan[
        "installation"
    ]

    assert installation[
        "application_user"
    ] == "kyouhan"

    assert installation[
        "application_user"
    ] != "root"

    assert installation[
        "log_directory"
    ] == "/var/log/aicontrolcenter"


def test_install_plan_targets_system_domain() -> None:
    module = load_module()

    plan = module.build_install_plan(
        ROOT
    )

    bootstrap_steps = [
        step
        for step in plan[
            "installation_plan"
        ]
        if step["step"]
        == "launchctl_bootstrap"
    ]

    assert len(bootstrap_steps) == 1

    assert bootstrap_steps[0][
        "domain"
    ] == "system"


def test_install_plan_targets_expected_service() -> None:
    module = load_module()

    plan = module.build_install_plan(
        ROOT
    )

    assert plan["installation"][
        "service"
    ] == (
        "system/"
        "com.aicontrolcenter.api.shadow"
    )
