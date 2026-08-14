from __future__ import annotations

import importlib.util
from pathlib import Path
import plistlib
import subprocess
from types import ModuleType
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/macos/launchd/application_scheduler_logs.py"
BOOTSTRAP_PATH = ROOT / "ops/macos/launchd/application_scheduler_bootstrap.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("application_scheduler_logs", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bootstrap() -> ModuleType:
    spec = importlib.util.spec_from_file_location("application_scheduler_bootstrap", BOOTSTRAP_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_paths(tmp_path: Path) -> tuple[Path, tuple[Path, Path], int, int]:
    directory = tmp_path / "aicontrolcenter"
    directory.mkdir(mode=0o755)
    directory.chmod(0o755)
    metadata = directory.lstat()
    return directory, (directory / "application-scheduler.stdout.log", directory / "application-scheduler.stderr.log"), metadata.st_uid, metadata.st_gid


def invoke(module: ModuleType, directory: Path, logs: Sequence[Path], uid: int, gid: int, **kwargs):
    return module.execute(
        log_directory=directory, log_paths=logs, root_uid=uid, wheel_gid=gid,
        service_uid=uid, staff_gid=gid, **kwargs,
    )


def make_valid(logs: Sequence[Path]) -> None:
    for path in logs:
        path.touch(mode=0o640)
        path.chmod(0o640)


def contract_result(*, ready: bool, inspection_error=None) -> dict:
    def inspected(path: str, *, directory: bool) -> dict:
        return {
            "path": path, "exists": True, "regular_file": not directory,
            "directory": directory, "symlink": False, "owner_matches": True,
            "group_matches": True, "mode_matches": True,
            "inspection_error": inspection_error, "valid": ready,
        }

    return {
        "parent": inspected("/var/log/aicontrolcenter", directory=True),
        "logs": [
            inspected("/var/log/aicontrolcenter/scheduler.stdout.log", directory=False),
            inspected("/var/log/aicontrolcenter/scheduler.stderr.log", directory=False),
        ],
        "scheduler_log_contract_ready": ready,
    }


def test_missing_logs_fail_read_only_readiness_without_mutation(tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    result = invoke(
        module, directory, logs, uid, gid, apply=False,
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert result["scheduler_log_readiness_gate_passed"] is False
    assert result["failure"]["step"] == "missing_scheduler_logs"
    assert not any(path.exists() for path in logs)
    assert result["write_operations_executed"] == 0


def test_valid_regular_logs_pass_readiness(tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    make_valid(logs)
    result = invoke(module, directory, logs, uid, gid, apply=False)
    assert result["scheduler_log_readiness_gate_passed"] is True
    assert all(item["valid"] for item in result["readiness"]["logs"])


@pytest.mark.parametrize("problem", ["symlink", "mode", "owner", "group"])
def test_invalid_existing_log_fails_closed(problem: str, tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    make_valid(logs)
    expected_uid, expected_gid = uid, gid
    if problem == "symlink":
        logs[0].unlink()
        logs[0].symlink_to(logs[1])
    elif problem == "mode":
        logs[0].chmod(0o644)
    elif problem == "owner":
        expected_uid += 1
    else:
        expected_gid += 1
    result = module.execute(
        apply=False, log_directory=directory, log_paths=logs,
        root_uid=uid, wheel_gid=gid, service_uid=expected_uid,
        staff_gid=expected_gid,
    )
    assert result["scheduler_log_readiness_gate_passed"] is False
    assert result["failure"]["step"] == "existing_log_contract"


def test_invalid_parent_contract_fails_closed(tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    directory.chmod(0o775)
    result = invoke(module, directory, logs, uid, gid, apply=False)
    assert result["failure"]["step"] == "log_parent_contract"


def test_provisioning_is_exact_and_contains_no_lifecycle_operation(tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    calls: list[list[str]] = []

    def provision(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        Path(argv[-1]).touch(mode=0o640)
        Path(argv[-1]).chmod(0o640)
        return subprocess.CompletedProcess(list(argv), 0, "", "")

    result = invoke(
        module, directory, logs, uid, gid, apply=True,
        effective_user_id=0, runner=provision,
    )
    assert result["scheduler_log_readiness_gate_passed"] is True
    assert [call[-1] for call in calls] == [str(path) for path in logs]
    assert all(call[:-1] == ["/usr/bin/install", "-o", "kyouhan", "-g", "staff", "-m", "0640", "/dev/null"] for call in calls)
    assert result["write_operations_executed"] == 2
    assert result["launchctl_operations_executed"] == 0
    assert result["retry_operations_executed"] == 0
    assert result["rollback_operations_executed"] == 0
    assert "launchctl" not in repr(result["commands"]).lower()


def test_wrong_existing_file_blocks_all_provisioning(tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    logs[0].touch(mode=0o644)
    logs[0].chmod(0o644)
    calls: list[list[str]] = []
    result = invoke(
        module, directory, logs, uid, gid, apply=True,
        effective_user_id=0, runner=lambda argv: calls.append(list(argv)),
    )
    assert result["failure"]["step"] == "existing_log_contract"
    assert calls == [] and not logs[1].exists()


def test_provisioning_requires_root_execution_precondition(
    tmp_path: Path,
) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    result = invoke(
        module, directory, logs, uid, gid, apply=True,
        effective_user_id=501,
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert result["failure"]["step"] == "executor_preconditions"
    assert result["write_operations_executed"] == 0
    assert not any(path.exists() for path in logs)


def test_unexpected_lstat_error_fails_closed_without_provision_plan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    original = module.Path.lstat

    def fail_one(path):
        if str(path) == str(logs[0]):
            raise PermissionError(13, "sensitive detail", str(path))
        return original(path)

    monkeypatch.setattr(module.Path, "lstat", fail_one)
    result = invoke(module, directory, logs, uid, gid, apply=False)
    assert result["scheduler_log_readiness_gate_passed"] is False
    assert result["failure"] == {"step": "filesystem_inspection", "paths": [str(logs[0])]}
    assert result["commands"] == []
    assert result["readiness"]["logs"][0]["inspection_error"] == {
        "error_type": "PermissionError", "errno": "EACCES",
    }
    assert "sensitive detail" not in repr(result)


@pytest.mark.parametrize("error", [PermissionError(13, "denied"), OSError(5, "io")])
def test_only_enoent_is_classified_as_missing(
    error: OSError, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    original = module.Path.lstat

    def fail_one(path):
        if str(path) == str(logs[0]):
            raise error
        return original(path)

    monkeypatch.setattr(module.Path, "lstat", fail_one)
    result = invoke(module, directory, logs, uid, gid, apply=False)
    assert result["failure"]["step"] == "filesystem_inspection"
    assert result["commands"] == []
    assert result["readiness"]["logs"][0]["exists"] is False
    assert result["readiness"]["logs"][0]["inspection_error"] is not None


def test_lifecycle_readiness_invokes_log_contract_and_fails_before_launchctl() -> None:
    module = load_bootstrap()
    calls = []

    def inspect(**kwargs):
        calls.append(kwargs)
        return contract_result(ready=False)

    result = module.execute(
        apply=True, effective_user_id=0, contract_inspector=inspect,
        contract_arguments={"marker": "bounded"},
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert calls == [{"marker": "bounded"}]
    assert result["failure"]["step"] == "scheduler_log_readiness"
    assert result["scheduler_lifecycle_readiness_gate_passed"] is False
    assert result["write_operations_executed"] == 0


def test_valid_logs_pass_lifecycle_readiness_without_writes(tmp_path: Path) -> None:
    logs_module = load_module()
    bootstrap = load_bootstrap()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    make_valid(logs)
    result = bootstrap.execute(
        apply=False, contract_inspector=logs_module.inspect_contract,
        contract_arguments={
            "log_directory": directory, "log_paths": logs,
            "root_uid": uid, "wheel_gid": gid,
            "service_uid": uid, "staff_gid": gid,
        },
        runner=lambda argv: subprocess.CompletedProcess(list(argv), 113, "", ""),
    )
    assert result["scheduler_lifecycle_readiness_gate_passed"] is True
    assert result["service_probe"] == {
        "performed": True, "returncode": 113, "eligible": True,
    }
    assert result["write_operations_executed"] == 0


@pytest.mark.parametrize(
    "inspection",
    [
        lambda: (_ for _ in ()).throw(PermissionError(13, "secret")),
        lambda: {},
        lambda: {"scheduler_log_contract_ready": "yes"},
        lambda: {"scheduler_log_contract_ready": True},
        lambda: contract_result(
            ready=False, inspection_error={"detail": "secret"},
        ),
    ],
)
def test_lifecycle_contract_failures_are_value_free_and_never_probe(
    inspection,
) -> None:
    module = load_bootstrap()
    result = module.execute(
        apply=True, effective_user_id=0, contract_inspector=inspection,
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert result["scheduler_log_readiness"] == {
        "scheduler_log_contract_ready": False,
    }
    assert result["write_operations_executed"] == 0
    assert "secret" not in repr(result)


def test_dry_run_and_apply_share_registration_eligibility_probe() -> None:
    module = load_bootstrap()
    calls: list[list[str]] = []

    def registered(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        return subprocess.CompletedProcess(list(argv), 0, "", "")

    for apply in (False, True):
        result = module.execute(
            apply=apply, effective_user_id=0, runner=registered,
            contract_inspector=lambda: contract_result(ready=True),
        )
        assert result["failure"] == {
            "step": "service_registration_probe", "state": "registered",
        }
        assert result["write_operations_executed"] == 0
    assert calls == [["/bin/launchctl", "print", module.SERVICE]] * 2


def test_indeterminate_probe_is_value_free_and_never_bootstraps() -> None:
    module = load_bootstrap()
    result = module.execute(
        apply=True, effective_user_id=0,
        runner=lambda argv: subprocess.CompletedProcess(list(argv), 77, "secret", "secret"),
        contract_inspector=lambda: contract_result(ready=True),
    )
    assert result["failure"] == {
        "step": "service_registration_probe", "state": "indeterminate",
    }
    assert result["service_probe"]["returncode"] is None
    assert result["write_operations_executed"] == 0
    assert "77" not in repr(result) and "secret" not in repr(result)


def test_lifecycle_executor_has_no_retry_or_rollback_path() -> None:
    module = load_bootstrap()
    calls: list[list[str]] = []

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        return subprocess.CompletedProcess(list(argv), 113 if len(calls) == 1 else 9, "", "")

    result = module.execute(
        apply=True, effective_user_id=0, runner=runner,
        contract_inspector=lambda: contract_result(ready=True),
    )
    assert len(calls) == 2
    assert result["failure"] == {"step": "bootstrap", "returncode": 9}
    assert result["retry_operations_executed"] == 0
    assert result["rollback_operations_executed"] == 0


def test_first_provision_failure_has_no_retry_or_rollback(tmp_path: Path) -> None:
    module = load_module()
    directory, logs, uid, gid = fixture_paths(tmp_path)
    calls: list[list[str]] = []

    def fail(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        return subprocess.CompletedProcess(list(argv), 7, "", "secret error")

    result = invoke(
        module, directory, logs, uid, gid, apply=True,
        effective_user_id=0, runner=fail,
    )
    assert len(calls) == 1
    assert result["failure"] == {"step": "provision_scheduler_log", "returncode": 7}
    assert result["retry_operations_executed"] == 0
    assert result["rollback_operations_executed"] == 0
    assert "secret error" not in repr(result)


def test_scheduler_plist_and_immutable_runner_contract_remain_intact() -> None:
    plist_path = ROOT / "ops/macos/launchd/com.aicontrolcenter.application-scheduler.plist"
    runner_path = ROOT / "ops/macos/launchd/run-application-scheduler-immutable-source.sh"
    with plist_path.open("rb") as stream:
        plist = plistlib.load(stream)
    runner = runner_path.read_text(encoding="utf-8")
    assert plist["StandardOutPath"] == "/var/log/aicontrolcenter/application-scheduler.stdout.log"
    assert plist["StandardErrorPath"] == "/var/log/aicontrolcenter/application-scheduler.stderr.log"
    assert plist["UserName"] == "kyouhan" and plist["GroupName"] == "staff"
    assert plist["EnvironmentVariables"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert 'export PYTHONDONTWRITEBYTECODE=1' in runner
    assert '"$PYTHON_PATH" -P -B "$VALIDATOR" validate' in runner
    assert 'exec "$PYTHON_PATH" -P -B -m core.scheduler.daemon' in runner
