from __future__ import annotations

from pathlib import Path
import plistlib
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PLIST = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "com.aicontrolcenter.api.shadow.plist"
)

RUNNER = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "run-shadow-daemon.sh"
)


def load_plist() -> dict[str, Any]:
    assert PLIST.is_file()

    with PLIST.open("rb") as stream:
        payload = plistlib.load(stream)

    assert isinstance(payload, dict)

    return payload


def test_contract_files_exist() -> None:
    assert PLIST.is_file()
    assert RUNNER.is_file()


def test_identity_contract() -> None:
    payload = load_plist()

    assert payload["Label"] == (
        "com.aicontrolcenter.api.shadow"
    )

    assert payload["UserName"] == "kyouhan"
    assert payload["GroupName"] == "staff"

    assert "WorkingDirectory" not in payload


def test_program_contract() -> None:
    payload = load_plist()

    assert payload["ProgramArguments"] == [
        "/bin/bash",
        (
            "/usr/local/libexec/"
            "aicontrolcenter/"
            "run-shadow-daemon.sh"
        ),
    ]


def test_lifecycle_contract() -> None:
    payload = load_plist()

    assert payload["RunAtLoad"] is True
    assert payload["KeepAlive"] is True
    assert payload["ProcessType"] == "Background"

    throttle = payload["ThrottleInterval"]

    assert isinstance(throttle, int)
    assert throttle >= 10


def test_log_contract() -> None:
    payload = load_plist()

    assert payload["StandardOutPath"] == (
        "/var/log/aicontrolcenter/"
        "shadow-daemon.stdout.log"
    )

    assert payload["StandardErrorPath"] == (
        "/var/log/aicontrolcenter/"
        "shadow-daemon.stderr.log"
    )


def test_environment_contract() -> None:
    payload = load_plist()

    environment = payload["EnvironmentVariables"]

    assert isinstance(environment, dict)

    assert environment["HOME"] == (
        "/Users/kyouhan"
    )

    assert environment["PYTHONUNBUFFERED"] == "1"

    path = str(environment["PATH"])

    assert "/usr/bin" in path
    assert "/bin" in path


def test_security_contract() -> None:
    payload = load_plist()

    assert payload["UserName"] != "root"

    arguments = payload["ProgramArguments"]

    assert isinstance(arguments, list)
    assert arguments[0] == "/bin/bash"


def test_network_contract_is_runner_owned() -> None:
    runner = RUNNER.read_text(
        encoding="utf-8"
    )

    assert "127.0.0.1" in runner
    assert "18100" in runner
