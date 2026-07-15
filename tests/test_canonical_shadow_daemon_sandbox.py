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
    / "canonical_shadow_daemon_sandbox.py"
)


def load_module() -> ModuleType:
    specification = (
        importlib.util.spec_from_file_location(
            "canonical_shadow_daemon_sandbox",
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


def test_sandbox_path_never_targets_system_root(
    tmp_path: Path,
) -> None:
    module = load_module()

    result = module.sandbox_path(
        tmp_path,
        Path(
            "/Library/LaunchDaemons/example.plist"
        ),
    )

    assert str(result).startswith(
        str(tmp_path)
    )

    assert result != Path(
        "/Library/LaunchDaemons/example.plist"
    )


def test_install_uses_sandbox_only(
    tmp_path: Path,
) -> None:
    module = load_module()

    result = module.install(
        ROOT,
        tmp_path,
    )

    assert result[
        "sandbox_install_gate_passed"
    ] is True

    assert result[
        "system_write_operations_executed"
    ] is False

    assert result[
        "launchctl_commands_executed"
    ] is False

    assert result["write_scope"] == (
        "sandbox_only"
    )

    assert all(
        result["checks"].values()
    )


def test_cycle_removes_new_assets_when_no_previous_install(
    tmp_path: Path,
) -> None:
    module = load_module()

    result = module.cycle(
        ROOT,
        tmp_path,
    )

    assert result[
        "sandbox_cycle_gate_passed"
    ] is True

    destinations = (
        module.sandbox_destinations(
            tmp_path
        )
    )

    assert not destinations[
        "plist"
    ].exists()

    assert not destinations[
        "runner"
    ].exists()


def test_cycle_restores_previous_assets(
    tmp_path: Path,
) -> None:
    module = load_module()

    destinations = (
        module.sandbox_destinations(
            tmp_path
        )
    )

    destinations["plist"].parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destinations["runner"].parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    previous_plist = b"previous-plist"
    previous_runner = b"previous-runner"

    destinations["plist"].write_bytes(
        previous_plist
    )

    destinations["runner"].write_bytes(
        previous_runner
    )

    destinations["plist"].chmod(0o600)
    destinations["runner"].chmod(0o700)

    result = module.cycle(
        ROOT,
        tmp_path,
    )

    assert result[
        "sandbox_cycle_gate_passed"
    ] is True

    assert destinations[
        "plist"
    ].read_bytes() == previous_plist

    assert destinations[
        "runner"
    ].read_bytes() == previous_runner

    assert module.file_mode(
        destinations["plist"]
    ) == "0600"

    assert module.file_mode(
        destinations["runner"]
    ) == "0700"


def test_cycle_result_is_json_serializable(
    tmp_path: Path,
) -> None:
    module = load_module()

    result = module.cycle(
        ROOT,
        tmp_path,
    )

    json.dumps(result)


def test_install_contract_modes(
    tmp_path: Path,
) -> None:
    module = load_module()

    result = module.install(
        ROOT,
        tmp_path,
    )

    assert result["checks"][
        "plist_mode_0644"
    ] is True

    assert result["checks"][
        "runner_mode_0755"
    ] is True

    assert result["checks"][
        "stdout_log_mode_0640"
    ] is True

    assert result["checks"][
        "stderr_log_mode_0640"
    ] is True
