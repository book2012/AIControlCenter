from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from types import ModuleType
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/macos/launchd/canonical_api_daemon_bootstrap.py"
RUNTIME_ID = "012345abcdef"
COMMIT = "a" * 40


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "canonical_api_daemon_bootstrap", MODULE_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed(argv: Sequence[str], returncode: int = 0):
    return subprocess.CompletedProcess(list(argv), returncode, "secret-output", "secret-error")


def fixture_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    runtime = tmp_path / "runtime"
    source = runtime / "sources" / RUNTIME_ID
    release = runtime / "venvs" / RUNTIME_ID
    source.joinpath("ops/macos/launchd").mkdir(parents=True)
    source.joinpath("ops/macos/runtime").mkdir(parents=True)
    release.mkdir(parents=True)
    source_plist = source / "ops/macos/launchd/com.aicontrolcenter.api.plist"
    source_runner = source / "ops/macos/runtime/run-canonical-api-immutable-source.sh"
    shutil.copy2(ROOT / "ops/macos/launchd/com.aicontrolcenter.api.plist", source_plist)
    shutil.copy2(ROOT / "ops/macos/runtime/run-canonical-api-immutable-source.sh", source_runner)
    source.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT + "\n")
    release.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT + "\n")
    source.joinpath(".aicontrolcenter-source-manifest.json").write_text(json.dumps({
        "schema_version": 1, "runtime_id": RUNTIME_ID, "source_commit": COMMIT,
        "git_tree": "b" * 40, "archive_sha256": "c" * 64,
        "content_sha256": "d" * 64, "artifact_root": str(source.resolve()),
        "build_status": "COMPLETE", "production_authorized": False,
    }))
    (runtime / "current").symlink_to(release)
    installed = tmp_path / "installed"
    installed.mkdir()
    plist = installed / "canonical.plist"
    runner = installed / "canonical-runner"
    shutil.copy2(source_plist, plist)
    shutil.copy2(source_runner, runner)
    plist.chmod(0o644)
    runner.chmod(0o755)
    return source, plist, runner


def invoke(module: ModuleType, source: Path, plist: Path, runner_path: Path, **kwargs):
    metadata = plist.lstat()
    return module.execute(
        root=source, installed_plist=plist, installed_runner=runner_path,
        expected_uid=kwargs.pop("expected_uid", metadata.st_uid),
        expected_gid=kwargs.pop("expected_gid", metadata.st_gid), **kwargs,
    )


def authorized(module: ModuleType, source: Path, plist: Path, runner_path: Path, command_runner):
    return invoke(
        module, source, plist, runner_path, apply=True,
        confirmation=module.LABEL,
        environment={"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"},
        effective_user_id=0, runner=command_runner,
    )


def test_dry_run_is_pure_and_ready(tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    result = invoke(
        module, source, plist, runner_path, apply=False,
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert result["canonical_bootstrap_gate_passed"] is True
    assert result["service_probe"]["performed"] is False
    assert result["result"]["performed"] is False
    assert result["write_operations_executed"] == 0


def test_mutable_repository_root_is_rejected(tmp_path: Path) -> None:
    module = load_module()
    _, plist, runner_path = fixture_tree(tmp_path)
    result = invoke(module, ROOT, plist, runner_path, apply=False)
    assert result["canonical_bootstrap_gate_passed"] is False
    assert result["immutable_source"]["immutable_source_context_valid"] is False


@pytest.mark.parametrize("problem", ["source_marker", "runtime_marker", "commit_mismatch"])
def test_marker_failures_close_gate(problem: str, tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    runtime_marker = source.parents[1] / "venvs" / RUNTIME_ID / ".aicontrolcenter-source-commit"
    if problem == "source_marker":
        source.joinpath(".aicontrolcenter-source-commit").unlink()
    elif problem == "runtime_marker":
        runtime_marker.unlink()
    else:
        runtime_marker.write_text("e" * 40 + "\n")
    result = invoke(module, source, plist, runner_path, apply=False)
    assert result["canonical_bootstrap_gate_passed"] is False
    assert result["immutable_source"]["immutable_source_context_valid"] is False


def test_current_pointer_mismatch_fails_closed(tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    current = source.parents[1] / "current"
    other = source.parents[1] / "venvs" / "fedcba987654"
    other.mkdir()
    current.unlink()
    current.symlink_to(other)
    result = invoke(module, source, plist, runner_path, apply=False)
    assert result["runtime_current"]["valid"] is False
    assert result["canonical_bootstrap_gate_passed"] is False


@pytest.mark.parametrize("problem", ["mismatch", "symlink", "mode", "owner"])
def test_installed_asset_failures_close_gate(problem: str, tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    expected_uid = plist.lstat().st_uid
    if problem == "mismatch":
        plist.write_bytes(b"different")
    elif problem == "symlink":
        runner_path.unlink()
        runner_path.symlink_to(source / "ops/macos/runtime/run-canonical-api-immutable-source.sh")
    elif problem == "mode":
        plist.chmod(0o600)
    else:
        expected_uid += 1
    result = invoke(
        module, source, plist, runner_path, apply=False,
        expected_uid=expected_uid,
    )
    assert result["installed_assets"]["valid"] is False
    assert result["canonical_bootstrap_gate_passed"] is False


@pytest.mark.parametrize("uid,environment,confirmation", [
    (501, {"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, "com.aicontrolcenter.api"),
    (0, {}, "com.aicontrolcenter.api"),
    (0, {"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, "wrong"),
])
def test_apply_requires_exact_authorization(uid: int, environment: dict[str, str], confirmation: str, tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    result = invoke(
        module, source, plist, runner_path, apply=True,
        effective_user_id=uid, environment=environment, confirmation=confirmation,
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert result["failure"]["step"] == "system_write_authorization"
    assert result["write_operations_executed"] == 0


@pytest.mark.parametrize("returncode,state", [(0, "registered"), (1, "indeterminate"), (125, "indeterminate")])
def test_non_absent_service_probe_blocks(returncode: int, state: str, tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    calls: list[list[str]] = []
    result = authorized(
        module, source, plist, runner_path,
        lambda argv: calls.append(list(argv)) or completed(argv, returncode),
    )
    assert result["failure"]["state"] == state
    assert calls == [["/bin/launchctl", "print", "system/com.aicontrolcenter.api"]]
    assert result["write_operations_executed"] == 0


def test_absent_probe_allows_exactly_one_bootstrap(tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    calls: list[list[str]] = []
    def success(argv: Sequence[str]):
        calls.append(list(argv))
        return completed(argv, 113 if len(calls) == 1 else 0)
    result = authorized(module, source, plist, runner_path, success)
    assert result["canonical_bootstrap_gate_passed"] is True
    assert calls == [
        ["/bin/launchctl", "print", "system/com.aicontrolcenter.api"],
        ["/bin/launchctl", "bootstrap", "system", "/Library/LaunchDaemons/com.aicontrolcenter.api.plist"],
    ]
    assert result["write_operations_executed"] == 1


def test_bootstrap_failure_has_no_second_mutation(tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    calls: list[list[str]] = []
    def fail(argv: Sequence[str]):
        calls.append(list(argv))
        return completed(argv, 113 if len(calls) == 1 else 7)
    result = authorized(module, source, plist, runner_path, fail)
    assert result["failure"] == {"step": "bootstrap", "returncode": 7}
    assert len(calls) == 2 and result["write_operations_executed"] == 1


@pytest.mark.parametrize("failure_at", ["probe", "bootstrap"])
def test_command_os_error_fails_closed_without_retry(
    failure_at: str, tmp_path: Path,
) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    calls: list[list[str]] = []

    def fail(argv: Sequence[str]):
        calls.append(list(argv))
        if failure_at == "probe" or len(calls) == 2:
            raise OSError("secret-command-error")
        return completed(argv, 113)

    result = authorized(module, source, plist, runner_path, fail)
    expected_calls = 1 if failure_at == "probe" else 2
    assert len(calls) == expected_calls
    assert result["canonical_bootstrap_gate_passed"] is False
    assert result["failure"]["error_type"] == "OSError"
    assert "secret-command-error" not in json.dumps(result)
    assert result["write_operations_executed"] == (
        0 if failure_at == "probe" else 1
    )


def test_command_inventory_and_secret_value_isolation(tmp_path: Path) -> None:
    module = load_module()
    source, plist, runner_path = fixture_tree(tmp_path)
    result = authorized(
        module, source, plist, runner_path,
        lambda argv: completed(argv, 113 if argv[1] == "print" else 7),
    )
    inventory = result["command"]["argv"]
    assert inventory == [
        "/bin/launchctl", "bootstrap", "system",
        "/Library/LaunchDaemons/com.aicontrolcenter.api.plist",
    ]
    serialized_inventory = json.dumps(inventory).lower()
    for forbidden in ("enable", "kickstart", "bootout", "disable", "retry", "rollback"):
        assert forbidden not in serialized_inventory
    serialized = json.dumps(result).lower()
    assert "secret-output" not in serialized and "secret-error" not in serialized


def test_production_defaults_remain_root_wheel() -> None:
    module = load_module()
    assert module.execute.__kwdefaults__["expected_uid"] == 0
    assert module.execute.__kwdefaults__["expected_gid"] is None
