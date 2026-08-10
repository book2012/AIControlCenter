from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


ROOT = Path(__file__).parents[2]

TOOL = (
    ROOT
    / "ops/macos/runtime/runtime-source-artifact.py"
)

WRAPPER = (
    ROOT
    / "ops/macos/runtime/run-shadow-daemon-immutable-source.sh"
)


def git(*args: str) -> str:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(ROOT),
            *args,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

    return completed.stdout.strip()


def unlock(root: Path) -> None:
    if not root.exists():
        return

    for current, directories, files in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current)

        try:
            current_path.chmod(0o700)
        except OSError:
            pass

        for name in directories:
            path = current_path / name

            if not path.is_symlink():
                try:
                    path.chmod(0o700)
                except OSError:
                    pass

        for name in files:
            path = current_path / name

            if not path.is_symlink():
                try:
                    path.chmod(0o600)
                except OSError:
                    pass


def run_tool(
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(TOOL),
            *args,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def test_build_validate_existing_destination_and_tamper():
    head = git(
        "rev-parse",
        "HEAD",
    )

    runtime_id = head[:12]

    base = Path(
        tempfile.mkdtemp(
            prefix="aicontrolcenter-a2-",
            dir="/private/tmp",
        )
    )

    runtime_root = base / "runtime"

    try:
        built = run_tool(
            "build",
            "--repository-root",
            str(ROOT),
            "--runtime-root",
            str(runtime_root),
            "--runtime-id",
            runtime_id,
            "--source-commit",
            head,
        )

        assert built.returncode == 0, (
            built.stdout
            + built.stderr
        )

        payload = json.loads(
            built.stdout
        )

        assert payload["status"] == "PASS"
        assert payload["operation"] == "BUILD"
        assert payload["runtime_id"] == runtime_id
        assert payload["source_commit"] == head
        assert payload["immutable"] is True
        assert payload["production_authorized"] is False

        assert (
            payload["operational_write_authorized"]
            is False
        )

        artifact = (
            runtime_root
            / "sources"
            / runtime_id
        )

        assert artifact.is_dir()
        assert not artifact.is_symlink()
        assert not (artifact / ".git").exists()

        required = (
            artifact
            / "core"
            / "api"
            / "shadow.py",
            artifact
            / "core"
            / "runtime"
            / "data_paths.py",
            artifact
            / "config"
            / "workers.yaml",
        )

        for path in required:
            assert path.is_file()

        assert (
            stat.S_IMODE(
                required[0].stat().st_mode
            )
            & 0o222
        ) == 0

        validated = run_tool(
            "validate",
            "--runtime-root",
            str(runtime_root),
            "--runtime-id",
            runtime_id,
            "--expected-source-commit",
            head,
        )

        assert validated.returncode == 0, (
            validated.stdout
            + validated.stderr
        )

        validation = json.loads(
            validated.stdout
        )

        assert validation["status"] == "PASS"
        assert validation["operation"] == "VALIDATE"

        second = run_tool(
            "build",
            "--repository-root",
            str(ROOT),
            "--runtime-root",
            str(runtime_root),
            "--runtime-id",
            runtime_id,
            "--source-commit",
            head,
        )

        assert second.returncode == 3

        assert (
            json.loads(
                second.stdout
            )["error"]
            == "SOURCE_DESTINATION_ALREADY_EXISTS"
        )

        entrypoint = required[0]

        entrypoint.chmod(0o644)

        with entrypoint.open(
            "ab"
        ) as stream:
            stream.write(
                b"\n# tamper\n"
            )

        tampered = run_tool(
            "validate",
            "--runtime-root",
            str(runtime_root),
            "--runtime-id",
            runtime_id,
            "--expected-source-commit",
            head,
        )

        assert tampered.returncode == 3

        error = json.loads(
            tampered.stdout
        )["error"]

        assert error in {
            "SOURCE_ARTIFACT_WRITABLE:core/api/shadow.py",
            "SOURCE_CONTENT_DIGEST_MISMATCH",
        }

    finally:
        unlock(base)

        shutil.rmtree(
            base,
            ignore_errors=True,
        )


def test_operational_write_requires_explicit_capability():
    head = git(
        "rev-parse",
        "HEAD",
    )

    runtime_id = head[:12]

    operational = (
        Path.home()
        / "Library"
        / "Application Support"
        / "AIControlCenter"
        / "runtime"
    )

    denied = run_tool(
        "build",
        "--repository-root",
        str(ROOT),
        "--runtime-root",
        str(operational),
        "--runtime-id",
        runtime_id,
        "--source-commit",
        head,
    )

    assert denied.returncode == 3

    assert (
        json.loads(
            denied.stdout
        )["error"]
        == "TEST_RUNTIME_ROOT_NOT_PRIVATE_TMP"
    )


def test_wrapper_enforces_source_and_state_contract():
    text = WRAPPER.read_text(
        encoding="utf-8"
    )

    assert 'cd "$ROOT"' not in text
    assert 'PYTHONPATH="$ROOT' not in text

    assert (
        'SOURCE_PARENT="$RUNTIME_ROOT/sources"'
        in text
    )

    assert 'cd "$SOURCE_REAL"' in text

    assert (
        'export PYTHONPATH="$SOURCE_REAL"'
        in text
    )

    assert "AICONTROLCENTER_DATA_ROOT" in text
    assert "content_sha256" in text

    assert (
        'root / "core" / "runtime" / "data_paths.py"'
        in text
    )

    assert "core.api.shadow:app" in text

    assert (
        '  "$PYTHON_PATH" \\\n'
        '  -P \\\n'
        '  -m uvicorn'
        in text
    )

    syntax = subprocess.run(
        [
            "/bin/bash",
            "-n",
            str(WRAPPER),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert syntax.returncode == 0, syntax.stderr
