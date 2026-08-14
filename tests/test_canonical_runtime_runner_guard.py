from __future__ import annotations

import os
from pathlib import Path
import pwd
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "ops/macos/runtime/run-canonical-api-immutable-source.sh"
VALID_ID = "012345abcdef"
COMMIT = "a" * 40


def prepare_runtime(tmp_path: Path, runtime_id: str = VALID_ID) -> tuple[Path, Path, dict[str, str]]:
    application = tmp_path / "application"
    runtime = application / "runtime"
    release = runtime / "venvs" / runtime_id
    source = runtime / "sources" / runtime_id
    data = application / "data"
    release.mkdir(parents=True)
    source.joinpath("ops/macos/runtime").mkdir(parents=True)
    data.mkdir(parents=True)
    release.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT)
    source.joinpath(".aicontrolcenter-source-commit").write_text(COMMIT)
    source.joinpath("ops/macos/runtime/runtime-source-artifact.py").write_text("# validator\n")
    source.joinpath("ops/macos/runtime/application.py").write_text("# app\n")
    invocation_log = tmp_path / "python-invocations"
    python = release / "bin/python"
    python.parent.mkdir()
    python.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{invocation_log}'\nexit 0\n")
    python.chmod(0o755)
    current = runtime / "current"
    current.symlink_to(release)
    environment = {
        **os.environ,
        "AICONTROLCENTER_APPLICATION_ROOT": str(application),
        "AICONTROLCENTER_RUN_USER": pwd.getpwuid(os.getuid()).pw_name,
    }
    return runtime, invocation_log, environment


def run(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", str(RUNNER)], env=environment, text=True, capture_output=True, check=False)


def test_direct_child_of_physical_venv_root_passes_containment(tmp_path: Path) -> None:
    _, log, environment = prepare_runtime(tmp_path)
    result = run(environment)
    assert result.returncode == 0, result.stderr
    invocations = log.read_text().splitlines()
    assert len(invocations) == 2
    assert "runtime-source-artifact.py validate" in invocations[0]
    assert "-m uvicorn ops.macos.runtime.application:app --host 127.0.0.1 --port 58081" in invocations[1]


def test_release_directly_under_runtime_fails(tmp_path: Path) -> None:
    runtime, log, environment = prepare_runtime(tmp_path)
    direct = runtime / VALID_ID
    direct.mkdir()
    (runtime / "current").unlink()
    (runtime / "current").symlink_to(direct)
    result = run(environment)
    assert result.returncode == 78
    assert "escaped runtime venv root" in result.stderr
    assert not log.exists()


def test_release_outside_runtime_fails(tmp_path: Path) -> None:
    runtime, log, environment = prepare_runtime(tmp_path)
    outside = tmp_path / "outside" / VALID_ID
    outside.mkdir(parents=True)
    (runtime / "current").unlink()
    (runtime / "current").symlink_to(outside)
    result = run(environment)
    assert result.returncode == 78
    assert "escaped runtime venv root" in result.stderr
    assert not log.exists()


def test_venv_root_symlink_fails(tmp_path: Path) -> None:
    runtime, log, environment = prepare_runtime(tmp_path)
    release = (runtime / "current").resolve()
    (runtime / "current").unlink()
    release.rename(tmp_path / "saved-release")
    (runtime / "venvs").rmdir()
    (runtime / "venvs").symlink_to(tmp_path)
    (runtime / "current").symlink_to(tmp_path / "saved-release")
    result = run(environment)
    assert result.returncode == 78
    assert "venv root is unavailable" in result.stderr
    assert not log.exists()


def test_release_symlink_escape_fails(tmp_path: Path) -> None:
    runtime, log, environment = prepare_runtime(tmp_path)
    outside = tmp_path / "outside" / VALID_ID
    outside.mkdir(parents=True)
    release = runtime / "venvs" / VALID_ID
    (runtime / "current").unlink()
    for child in sorted(release.rglob("*"), reverse=True):
        child.unlink() if child.is_file() else child.rmdir()
    release.rmdir()
    release.symlink_to(outside)
    (runtime / "current").symlink_to(release)
    result = run(environment)
    assert result.returncode == 78
    assert "escaped runtime venv root" in result.stderr
    assert not log.exists()


@pytest.mark.parametrize("runtime_id", ["012345abcdeg", "012345abcde", "012345ABCDEF"])
def test_malformed_runtime_id_fails(tmp_path: Path, runtime_id: str) -> None:
    _, log, environment = prepare_runtime(tmp_path, runtime_id)
    result = run(environment)
    assert result.returncode == 78
    assert "identity is invalid" in result.stderr
    assert not log.exists()
