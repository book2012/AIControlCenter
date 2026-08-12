from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from types import ModuleType
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/macos/launchd/canonical_api_daemon_executor.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("canonical_api_daemon_executor", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed(argv: Sequence[str], returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(argv), returncode, "", "failure" if returncode else "")


def authorized(module: ModuleType, runner, **kwargs):
    return module.execute(root=ROOT, apply=True, confirmation=module.LABEL,
                          environment={"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"},
                          effective_user_id=0, runner=runner,
                          installed_plist=kwargs.get("installed_plist", Path("/nonexistent/plist")),
                          installed_runner=kwargs.get("installed_runner", Path("/nonexistent/runner")))


def test_dry_run_is_pure_and_commands_are_deterministic() -> None:
    module = load_module()
    result = module.execute(root=ROOT, apply=False, runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)))
    assert result["canonical_executor_gate_passed"] is True
    assert result["write_operations_executed"] is False and result["results"] == []
    argv = [command["argv"] for command in result["commands"]]
    assert argv[-3:] == [
        ["/bin/launchctl", "bootstrap", "system", "/Library/LaunchDaemons/com.aicontrolcenter.api.plist"],
        ["/bin/launchctl", "enable", "system/com.aicontrolcenter.api"],
        ["/bin/launchctl", "kickstart", "system/com.aicontrolcenter.api"],
    ]
    text = repr(argv)
    assert "bootout" not in text and "shadow" not in text and "rollback" not in text


def test_apply_requires_each_authorization_factor() -> None:
    module = load_module()
    cases = [
        (501, {"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, module.LABEL),
        (0, {}, module.LABEL),
        (0, {"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, "wrong"),
    ]
    for uid, environment, confirmation in cases:
        result = module.execute(root=ROOT, apply=True, effective_user_id=uid, environment=environment,
                                confirmation=confirmation, runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)))
        assert result["failure"]["step"] == "system_write_authorization"
        assert result["write_operations_executed"] is False


def test_registered_service_blocks_before_writes() -> None:
    module = load_module()
    calls: list[list[str]] = []
    def registered(argv: Sequence[str]):
        calls.append(list(argv)); return completed(argv, 0)
    result = authorized(module, registered)
    assert result["failure"]["blockers"] == ["service_registered"] and len(calls) == 1
    assert result["write_operations_executed"] is False


def test_unexpected_service_probe_results_fail_closed_before_writes() -> None:
    module = load_module()
    for returncode in (125, 1):
        calls: list[list[str]] = []
        def indeterminate(argv: Sequence[str], rc: int = returncode):
            calls.append(list(argv)); return completed(argv, rc)
        result = authorized(module, indeterminate)
        assert result["failure"] == {
            "step": "service_registration_probe",
            "returncode": returncode,
            "detail": "Canonical service registration state is indeterminate",
        }
        assert result["write_operations_executed"] is False
        assert result["results"] == []
        assert calls == [["/bin/launchctl", "print", "system/com.aicontrolcenter.api"]]


def test_preexisting_normal_assets_block_before_writes(tmp_path: Path) -> None:
    module = load_module()
    for key in ("installed_plist", "installed_runner"):
        existing = tmp_path / key
        existing.write_text("x")
        calls: list[list[str]] = []
        def absent(argv: Sequence[str]):
            calls.append(list(argv)); return completed(argv, 113)
        result = authorized(module, absent, **{key: existing})
        assert result["preflight_inspection"]["service_confirmed_absent"] is True
        assert result["failure"]["blockers"] == [key + "_exists"]
        assert len(calls) == 1 and result["write_operations_executed"] is False


def test_dangling_asset_symlinks_block_before_writes(tmp_path: Path) -> None:
    module = load_module()
    for key in ("installed_plist", "installed_runner"):
        dangling = tmp_path / key
        dangling.symlink_to(tmp_path / (key + "-missing"))
        calls: list[list[str]] = []
        def absent(argv: Sequence[str]):
            calls.append(list(argv)); return completed(argv, 113)
        result = authorized(module, absent, **{key: dangling})
        assert result["failure"]["blockers"] == [key + "_exists"]
        assert len(calls) == 1 and result["write_operations_executed"] is False


def test_first_install_order_and_failure_stops_immediately() -> None:
    module = load_module()
    calls: list[list[str]] = []
    def success(argv: Sequence[str]):
        calls.append(list(argv)); return completed(argv, 113 if argv[1] == "print" else 0)
    result = authorized(module, success)
    assert result["canonical_executor_gate_passed"] is True
    assert result["preflight_inspection"]["service_confirmed_absent"] is True
    assert calls[0] == ["/bin/launchctl", "print", "system/com.aicontrolcenter.api"]
    assert calls[1:] == [command["argv"] for command in result["commands"]]
    command_text = repr(calls)
    assert "bootout" not in command_text
    assert "shadow" not in command_text
    assert "rollback" not in command_text

    calls.clear()
    def fail_first_write(argv: Sequence[str]):
        calls.append(list(argv)); return completed(argv, 113 if len(calls) == 1 else 7)
    result = authorized(module, fail_first_write)
    assert result["failure"]["returncode"] == 7
    assert len(calls) == 2 and len(result["results"]) == 1
    assert result["write_operations_executed"] is True
    assert calls[1] == result["commands"][0]["argv"]
