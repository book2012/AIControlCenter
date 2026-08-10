from __future__ import annotations

import re
import subprocess
from pathlib import Path


RUNNER = Path(
    "ops/macos/launchd/run-shadow-daemon.sh"
)


def runner_source() -> str:
    return RUNNER.read_text(encoding="utf-8")


def test_runner_exports_release_identity() -> None:
    source = runner_source()

    assert (
        "export AICONTROLCENTER_SOURCE_COMMIT"
        in source
    )
    assert (
        "export AICONTROLCENTER_RUNTIME_RELEASE"
        in source
    )
    assert (
        "export AICONTROLCENTER_DATA_ROOT"
        in source
    )


def test_runner_reads_commit_from_release_metadata() -> None:
    source = runner_source()

    assert (
        ".aicontrolcenter-source-commit"
        in source
    )
    assert (
        "$AICONTROLCENTER_CURRENT_RELEASE/"
        ".aicontrolcenter-source-commit"
        in source
    )


def test_runner_resolves_current_release() -> None:
    source = runner_source()

    assert (
        "AICONTROLCENTER_RUNTIME_LINK"
        in source
    )
    assert (
        "os.path.realpath"
        in source
    )
    assert (
        'basename "$AICONTROLCENTER_CURRENT_RELEASE"'
        in source
    )


def test_runner_uses_application_state_data_root() -> None:
    source = runner_source()

    assert (
        "$AICONTROLCENTER_APPLICATION_ROOT/data"
        in source
    )
    assert (
        'mkdir -p "$AICONTROLCENTER_DATA_ROOT"'
        in source
    )


def test_runner_validates_full_lowercase_git_sha() -> None:
    source = runner_source()

    assert (
        "grep -Eq '^[0-9a-f]{40}$'"
        in source
    )
    assert (
        "source commit metadata is invalid"
        in source
    )



def test_runner_fails_when_metadata_is_missing() -> None:
    source = runner_source()

    assert (
        'if [ ! -f "$AICONTROLCENTER_SOURCE_COMMIT_FILE" ]'
        in source
    )
    assert (
        "source commit metadata is missing"
        in source
    )


def test_runner_validates_runtime_release_identifier() -> None:
    source = runner_source()

    assert (
        'case "$AICONTROLCENTER_RUNTIME_RELEASE" in'
        in source
    )
    assert (
        '"|*[!0-9a-f]*'
        in source
    )
    assert (
        "runtime release identity is invalid"
        in source
    )


def test_identity_is_exported_before_uvicorn_exec() -> None:
    source = runner_source()

    identity_position = source.index(
        "export AICONTROLCENTER_SOURCE_COMMIT"
    )
    exec_position = source.index(
        'exec /usr/bin/python3 "$SECRET_DELIVERY" exec'
    )
    uvicorn_position = source.index(
        "-m uvicorn"
    )

    assert identity_position < exec_position
    assert exec_position < uvicorn_position


def test_uvicorn_exec_command_is_preserved() -> None:
    source = runner_source()

    expected = (
        'exec /usr/bin/python3 "$SECRET_DELIVERY" exec --provider "$ACTIVE_PROVIDER" -- \\\n'
        '  "$PYTHON_PATH" \\\n'
        '  -P \\\n'
        '  -m uvicorn \\\n'
        '  core.api.shadow:app \\\n'
        '  --host "$HOST" \\\n'
        '  --port "$PORT"'
    )

    assert expected in source
    assert source.count(
        'exec /usr/bin/python3 "$SECRET_DELIVERY" exec'
    ) == 1


def test_runner_uses_active_runtime_and_matching_immutable_source() -> None:
    source = runner_source()

    assert 'CURRENT_RUNTIME="$RUNTIME_ROOT/current"' in source
    assert 'RUNTIME_ID="$(' in source
    assert 'SOURCE_ROOT="$SOURCE_PARENT/$RUNTIME_ID"' in source
    assert 'RUNTIME_SOURCE_MARKER="$RUNTIME_TARGET/.aicontrolcenter-source-commit"' in source
    assert 'SOURCE_SOURCE_MARKER="$SOURCE_REAL/.aicontrolcenter-source-commit"' in source
    assert "Runtime/source identity mismatch" in source
    assert '"$PYTHON_PATH" \\\n    -P \\\n    - "$SOURCE_REAL"' in source


def test_runner_prohibits_mutable_repository_serving() -> None:
    source = runner_source()

    assert "/Users/kyouhan/AIControlCenter" not in source
    assert 'cd "$ROOT"' not in source
    assert 'PYTHONPATH="$ROOT' not in source
    assert "unset PYTHONPATH" in source
    assert 'cd "$SOURCE_REAL"' in source
    assert 'export PYTHONPATH="$SOURCE_REAL"' in source
    assert source.index("unset PYTHONPATH") < source.index('cd "$SOURCE_REAL"')
    assert source.index('cd "$SOURCE_REAL"') < source.index(
        'exec /usr/bin/python3 "$SECRET_DELIVERY" exec'
    )


def test_runtime_template_and_canonical_wrapper_do_not_drift() -> None:
    template = Path(
        "ops/macos/runtime/run-shadow-daemon-immutable-source.sh"
    ).read_text(encoding="utf-8")

    assert runner_source() == template


def test_runner_does_not_depend_on_git_checkout() -> None:
    source = runner_source()

    forbidden = {
        "git rev-parse",
        "rev-parse --short=12 HEAD",
        "git describe",
        ".git/HEAD",
        "status --porcelain",
        "Runtime commit does not match Git HEAD",
        "Git working tree is not clean",
        "AIControlCenter repository not found",
    }

    assert forbidden.isdisjoint(source)


def test_runner_uses_exit_for_fail_closed_guards() -> None:
    source = runner_source()

    assert "return 78" not in source
    assert source.count("exit 78") >= 4


def test_runner_can_restart_independently_of_git_head() -> None:
    source = runner_source()

    assert "EXPECTED_COMMIT=" not in source
    assert "rev-parse --short=12 HEAD" not in source
    assert ".aicontrolcenter-source-commit" in source



def test_runner_shell_syntax_is_valid() -> None:
    result = subprocess.run(
        [
            "zsh",
            "-n",
            str(RUNNER),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
