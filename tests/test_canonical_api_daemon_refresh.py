from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import ModuleType
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/macos/launchd/canonical_api_daemon_refresh.py"
RUNTIME_ID = "012345abcdef"
COMMIT = "a" * 40


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("canonical_api_daemon_refresh", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed(argv: Sequence[str], returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(argv), returncode, "", "failure" if returncode else "")


def assets(tmp_path: Path) -> tuple[Path, Path]:
    plist, runner = tmp_path / "installed.plist", tmp_path / "installed-runner"
    plist.write_text("plist")
    runner.write_text("runner")
    plist.chmod(0o644)
    runner.chmod(0o755)
    return plist, runner


def immutable_source(tmp_path: Path, runtime_id: str = RUNTIME_ID) -> Path:
    runtime = tmp_path / "runtime"
    source = runtime / "sources" / runtime_id
    release = runtime / "venvs" / runtime_id
    source.joinpath("ops/macos/launchd").mkdir(parents=True)
    source.joinpath("ops/macos/runtime").mkdir(parents=True)
    release.mkdir(parents=True)
    shutil.copy2(ROOT / "ops/macos/launchd/com.aicontrolcenter.api.plist", source / "ops/macos/launchd")
    shutil.copy2(ROOT / "ops/macos/runtime/run-canonical-api-immutable-source.sh", source / "ops/macos/runtime")
    source.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT + "\n", encoding="ascii")
    release.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT + "\n", encoding="ascii")
    manifest = {
        "schema_version": 1, "runtime_id": runtime_id, "source_commit": COMMIT,
        "git_tree": "b" * 40, "archive_sha256": "c" * 64,
        "content_sha256": "d" * 64, "artifact_root": str(source.resolve()),
        "build_status": "COMPLETE", "production_authorized": False,
    }
    source.joinpath(".aicontrolcenter-source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return source


def authorized(module: ModuleType, source: Path, command_runner, plist: Path, installed_runner: Path):
    reference_metadata = None
    for candidate in (plist, installed_runner):
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if candidate.is_symlink():
            continue
        if candidate.is_file():
            reference_metadata = metadata
            break

    assert reference_metadata is not None

    return module.execute(
        root=source, apply=True, confirmation=module.LABEL,
        environment={"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, effective_user_id=0,
        runner=command_runner, installed_plist=plist, installed_runner=installed_runner,
        expected_uid=reference_metadata.st_uid, expected_gid=reference_metadata.st_gid,
    )


def test_dry_run_is_pure_and_uses_exact_immutable_sources(tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    result = module.execute(root=source, apply=False, runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)))
    assert result["canonical_refresh_gate_passed"] is True
    assert result["immutable_source"]["immutable_source_context_valid"] is True
    assert result["write_operations_executed"] is False
    assert result["results"] == [] and result["preflight_state"] == {"performed": False}
    commands = [item["argv"] for item in result["commands"]]
    assert commands == [
        ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0755", str(source / "ops/macos/runtime/run-canonical-api-immutable-source.sh"), "/usr/local/libexec/aicontrolcenter/run-canonical-api-immutable-source.sh"],
        ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0644", str(source / "ops/macos/launchd/com.aicontrolcenter.api.plist"), "/Library/LaunchDaemons/com.aicontrolcenter.api.plist"],
    ]
    text = repr(commands).lower()
    assert "launchctl" not in text and "shadow" not in text and "runtime/current" not in text


def test_mutable_repository_root_dry_run_is_not_refresh_ready() -> None:
    module = load_module()
    result = module.execute(root=ROOT, apply=False, runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)))
    assert result["canonical_refresh_gate_passed"] is False
    assert result["immutable_source"]["immutable_source_context_valid"] is False


@pytest.mark.parametrize("problem", ["source_symlink", "malformed_id", "commit_mismatch", "missing_marker", "malformed_marker", "venv_symlink", "venv_escape"])
def test_invalid_immutable_source_context_fails_closed(problem: str, tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path, "012345abcdeg" if problem == "malformed_id" else RUNTIME_ID)
    runtime = source.parents[1]
    if problem == "source_symlink":
        target = tmp_path / "saved-source"
        source.rename(target)
        source.symlink_to(target, target_is_directory=True)
    elif problem == "commit_mismatch":
        (runtime / "venvs" / RUNTIME_ID / ".aicontrolcenter-source-commit").write_text("e" * 40 + "\n")
    elif problem == "missing_marker":
        (source / ".aicontrolcenter-source-commit").unlink()
    elif problem == "malformed_marker":
        (source / ".aicontrolcenter-source-commit").write_text("BAD\n")
    elif problem in {"venv_symlink", "venv_escape"}:
        release = runtime / "venvs" / RUNTIME_ID
        shutil.rmtree(release)
        target = (runtime / "outside" / RUNTIME_ID) if problem == "venv_escape" else (tmp_path / "release")
        target.mkdir(parents=True)
        target.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT + "\n")
        release.symlink_to(target, target_is_directory=True)
    result = module.execute(root=source, apply=False, runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)))
    assert result["canonical_refresh_gate_passed"] is False
    assert result["immutable_source"]["immutable_source_context_valid"] is False


def test_invalid_immutable_source_blocks_apply_before_external_commands(tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    (source / ".aicontrolcenter-source-commit").unlink()
    result = module.execute(
        root=source, apply=True, confirmation=module.LABEL,
        environment={"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, effective_user_id=0,
        runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)),
    )
    assert result["failure"] == {"step": "immutable_source_context"}
    assert result["preflight_state"] == {"performed": False}
    assert result["write_operations_executed"] is False


@pytest.mark.parametrize("uid,environment,confirmation", [
    (501, {"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, "com.aicontrolcenter.api"),
    (0, {}, "com.aicontrolcenter.api"),
    (0, {"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, "wrong"),
])
def test_apply_requires_all_authorization(uid: int, environment: dict[str, str], confirmation: str, tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    result = module.execute(root=source, apply=True, effective_user_id=uid, environment=environment,
                            confirmation=confirmation, runner=lambda argv: (_ for _ in ()).throw(AssertionError(argv)))
    assert result["failure"]["step"] == "system_write_authorization"
    assert result["write_operations_executed"] is False


@pytest.mark.parametrize("returncode,detail", [(0, "Canonical service is registered"), (125, "Canonical service registration state is indeterminate"), (1, "Canonical service registration state is indeterminate")])
def test_non_113_probe_blocks(returncode: int, detail: str, tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    plist, runner = assets(tmp_path)
    calls: list[list[str]] = []
    result = authorized(module, source, lambda argv: calls.append(list(argv)) or completed(argv, returncode), plist, runner)
    assert result["failure"] == {"step": "service_registration_probe", "returncode": returncode, "detail": detail}
    assert calls == [["/bin/launchctl", "print", "system/com.aicontrolcenter.api"]]
    assert result["write_operations_executed"] is False


def test_113_probe_allows_valid_refresh(tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    plist, runner = assets(tmp_path)
    calls: list[list[str]] = []
    def success(argv: Sequence[str]):
        calls.append(list(argv))
        return completed(argv, 113 if len(calls) == 1 else 0)
    result = authorized(module, source, success, plist, runner)
    assert result["canonical_refresh_gate_passed"] is True
    assert result["preflight_state"]["service_confirmed_absent"] is True
    assert calls[1:] == [command["argv"] for command in result["commands"]]


@pytest.mark.parametrize("problem", ["missing", "dangling", "mode"])
def test_invalid_installed_asset_blocks(problem: str, tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    plist, runner = assets(tmp_path)
    if problem == "missing":
        plist.unlink()
    elif problem == "dangling":
        runner.unlink(); runner.symlink_to(tmp_path / "absent")
    else:
        plist.chmod(0o600)
    calls: list[list[str]] = []
    result = authorized(module, source, lambda argv: calls.append(list(argv)) or completed(argv, 113), plist, runner)
    assert result["failure"]["step"] == "installed_asset_validation"
    assert len(calls) == 1 and result["write_operations_executed"] is False


def test_wrong_owner_blocks(tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    plist, runner = assets(tmp_path)
    result = module.execute(
        root=source, apply=True, confirmation=module.LABEL,
        environment={"AICONTROLCENTER_ALLOW_SYSTEM_WRITE": "1"}, effective_user_id=0,
        runner=lambda argv: completed(argv, 113), installed_plist=plist, installed_runner=runner,
        expected_uid=plist.lstat().st_uid + 1, expected_gid=plist.lstat().st_gid,
    )
    assert result["failure"]["step"] == "installed_asset_validation"


def test_first_write_failure_stops_immediately(tmp_path: Path) -> None:
    module = load_module()
    source = immutable_source(tmp_path)
    plist, runner = assets(tmp_path)
    calls: list[list[str]] = []
    def fail(argv: Sequence[str]):
        calls.append(list(argv))
        return completed(argv, 113 if len(calls) == 1 else 7)
    result = authorized(module, source, fail, plist, runner)
    assert result["failure"]["returncode"] == 7
    assert len(calls) == 2 and len(result["results"]) == 1
    assert result["write_operations_executed"] is True
