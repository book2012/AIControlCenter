from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/macos/runtime/bootstrap-production-runtime.sh"
COMMIT = "a" * 40


def run_script(
    tmp_path: Path,
    *arguments: str,
    root: Path | None = None,
    extra_env: dict[str, str] | None = None,
):
    runtime_root = tmp_path / "runtime"
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(tmp_path / "home"),
            "AICONTROLCENTER_ROOT": str(root or ROOT),
            "AICONTROLCENTER_RUNTIME_ROOT": str(runtime_root),
        }
    )
    environment.update(extra_env or {})
    result = subprocess.run(
        ["bash", str(SCRIPT), *arguments],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, runtime_root


def make_build_fixture(tmp_path: Path, dependency_file: str = "requirements.txt"):
    app_root = tmp_path / "build-app"
    install_metadata_module(app_root)
    (app_root / "app.py").write_text("application = object()\n", encoding="utf-8")
    (app_root / dependency_file).write_text("", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(app_root)], check=True)
    subprocess.run(["git", "-C", str(app_root), "add", "."], check=True)
    subprocess.run(
        [
            "git", "-C", str(app_root), "-c", "user.name=Test",
            "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(app_root), "rev-parse", "HEAD"], text=True
    ).strip()
    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps(
            {
                "runtime_contract_gate_passed": True,
                "repository": {"commit": commit},
                "production_candidate": {
                    "dependency_file": dependency_file,
                    "runtime_target": "app:application",
                    "test_command": "python -m pytest -q",
                },
            }
        ),
        encoding="utf-8",
    )
    tools = tmp_path / "tools"
    tools.mkdir()
    fake_python = tools / "python3.12"
    fake_python.write_text(
        "#!/bin/sh\n"
        'if [ "$1 $2" = "-m venv" ]; then\n'
        '  mkdir -p "$3/bin"\n'
        "  sed 's|@PYTHON@|" + sys.executable + "|g' >\"$3/bin/python\" <<'WRAPPER'\n"
        "#!/bin/sh\n"
        'if [ "$1 $2" = "-m pip" ]; then\n'
        '  if [ "$3" = "list" ]; then printf "[]\\n"; fi\n'
        "  exit 0\n"
        "fi\n"
        'if [ "$1 $2" = "-m pytest" ]; then exit 0; fi\n'
        'exec "@PYTHON@" "$@"\n'
        "WRAPPER\n"
        '  chmod 755 "$3/bin/python"\n'
        "  exit 0\n"
        "fi\n"
        f'exec "{sys.executable}" "$@"\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    environment = {"PATH": f"{tools}:{os.environ['PATH']}"}
    return app_root, contract, commit, environment


def install_metadata_module(root: Path) -> None:
    package = root / "core/runtime"
    package.mkdir(parents=True)
    (root / "core/__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy(ROOT / "core/runtime/metadata.py", package / "metadata.py")
    shutil.copy(
        ROOT / "core/runtime/metadata_generator.py",
        package / "metadata_generator.py",
    )


def make_release(
    tmp_path: Path,
    *,
    commit: str = COMMIT,
    marker: bytes | None = None,
    metadata: bool = True,
) -> tuple[Path, Path, Path]:
    app_root = tmp_path / "app"
    install_metadata_module(app_root)
    runtime_root = tmp_path / "runtime"
    release = runtime_root / "venvs/release-a"
    (release / "bin").mkdir(parents=True)
    runtime_python = release / "bin/python"
    runtime_python.write_text(
        "#!/bin/sh\n"
        'if [ "$1 $2" = "-m pip" ]; then\n'
        '  if [ "$3" = "list" ]; then printf "[]\\n"; fi\n'
        "  exit 0\n"
        "fi\n"
        f'exec "{sys.executable}" "$@"\n',
        encoding="utf-8",
    )
    runtime_python.chmod(0o755)
    if marker is not None:
        (release / ".aicontrolcenter-source-commit").write_bytes(marker)
    if metadata:
        (release / "metadata.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "commit": commit,
                    "short_commit": commit[:12],
                    "runtime_mode": "shadow",
                    "created_at": "2026-08-04T00:00:00Z",
                }
            ),
            encoding="utf-8",
        )
    return app_root, runtime_root, release


def test_shell_syntax() -> None:
    assert subprocess.run(["bash", "-n", str(SCRIPT)], check=False).returncode == 0


@pytest.mark.parametrize("arguments", [(), ("--mode", "invalid")])
def test_missing_or_invalid_mode_fails_closed(tmp_path: Path, arguments) -> None:
    result, _ = run_script(tmp_path, *arguments)
    assert result.returncode != 0
    assert "Usage:" in result.stderr


@pytest.mark.parametrize(
    ("marker", "metadata"),
    [
        (None, True),
        (b"not-a-commit\n", True),
        (("b" * 40 + "\n").encode(), True),
        ((COMMIT + "\n").encode(), False),
    ],
)
def test_activate_rejects_invalid_identity(
    tmp_path: Path, marker: bytes | None, metadata: bool
) -> None:
    app_root, _, release = make_release(tmp_path, marker=marker, metadata=metadata)
    result, runtime_root = run_script(
        tmp_path,
        "--mode",
        "activate",
        "--release",
        str(release),
        "--expected-source-commit",
        COMMIT,
        root=app_root,
    )
    assert result.returncode != 0
    assert not (runtime_root / "current").exists()


def test_activate_rejects_release_outside_venv_root(tmp_path: Path) -> None:
    app_root, _, release = make_release(tmp_path, marker=(COMMIT + "\n").encode())
    outside = tmp_path / "outside"
    shutil.copytree(release, outside, symlinks=True)
    result, runtime_root = run_script(
        tmp_path,
        "--mode",
        "activate",
        "--release",
        str(outside),
        "--expected-source-commit",
        COMMIT,
        root=app_root,
    )
    assert result.returncode != 0
    assert not (runtime_root / "current").exists()


def test_activate_rejects_repository_venv(tmp_path: Path) -> None:
    app_root, _, release = make_release(tmp_path, marker=(COMMIT + "\n").encode())
    repository_venv = app_root / ".venv"
    shutil.copytree(release, repository_venv, symlinks=True)
    result, _ = run_script(
        tmp_path,
        "--mode",
        "activate",
        "--release",
        str(repository_venv),
        "--expected-source-commit",
        COMMIT,
        root=app_root,
    )
    assert result.returncode != 0


def test_successful_activation_atomically_switches_and_reports_targets(tmp_path: Path) -> None:
    app_root, runtime_root, release = make_release(
        tmp_path, marker=(COMMIT + "\n").encode()
    )
    previous = runtime_root / "venvs/previous"
    previous.mkdir(parents=True)
    (runtime_root / "current").symlink_to(previous)
    result, _ = run_script(
        tmp_path,
        "--mode",
        "activate",
        "--release",
        str(release),
        "--expected-source-commit",
        COMMIT,
        root=app_root,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "activate"
    assert report["activated"] is True
    assert report["runtime"]["current_target_before"] == str(previous)
    assert report["runtime"]["current_target_after"] == str(release)
    assert os.readlink(runtime_root / "current") == str(release)
    assert not list(runtime_root.glob(".current.*.tmp"))


def test_builder_contains_no_service_operations_and_build_has_no_activation() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "launchctl" not in content
    assert "restart" not in content
    build_body = content.split("run_build_mode() {", 1)[1].split("\n}", 1)[0]
    assert "activate_runtime" not in build_body
    assert "RUNTIME_ROOT/current" not in build_body


def test_build_finalizes_metadata_without_changing_current(tmp_path: Path) -> None:
    app_root, contract, commit, environment = make_build_fixture(tmp_path)
    runtime_root = tmp_path / "runtime"
    previous = runtime_root / "venvs/previous"
    previous.mkdir(parents=True)
    (runtime_root / "current").symlink_to(previous)
    result, _ = run_script(
        tmp_path,
        "--mode", "build", "--contract", str(contract),
        root=app_root,
        extra_env=environment,
    )
    assert result.returncode == 0, result.stderr
    release = runtime_root / "venvs" / commit[:12]
    assert (release / ".aicontrolcenter-source-commit").read_bytes() == (
        commit + "\n"
    ).encode()
    assert json.loads((release / "metadata.json").read_text())["commit"] == commit
    assert os.readlink(runtime_root / "current") == str(previous)
    report = json.loads(result.stdout)
    assert report["mode"] == "build"
    assert report["activated"] is False
    assert report["runtime"]["current_unchanged"] is True


def test_existing_finalized_release_is_not_modified(tmp_path: Path) -> None:
    app_root, contract, commit, environment = make_build_fixture(tmp_path)
    release = tmp_path / "runtime/venvs" / commit[:12]
    release.mkdir(parents=True)
    sentinel = release / "sentinel"
    sentinel.write_text("unchanged", encoding="utf-8")
    result, _ = run_script(
        tmp_path, "--mode", "build", "--contract", str(contract),
        root=app_root, extra_env=environment,
    )
    assert result.returncode != 0
    assert sentinel.read_text(encoding="utf-8") == "unchanged"


def test_build_failure_removes_only_owned_staging(tmp_path: Path) -> None:
    app_root, contract, _, environment = make_build_fixture(tmp_path, "deps.unsupported")
    preserved = tmp_path / "runtime/venvs/preserved"
    preserved.mkdir(parents=True)
    (preserved / "sentinel").write_text("keep", encoding="utf-8")
    result, runtime_root = run_script(
        tmp_path, "--mode", "build", "--contract", str(contract),
        root=app_root, extra_env=environment,
    )
    assert result.returncode != 0
    assert (preserved / "sentinel").read_text(encoding="utf-8") == "keep"
    assert not list((runtime_root / "venvs").glob(".staging-*"))
