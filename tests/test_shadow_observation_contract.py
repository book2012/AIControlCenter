from __future__ import annotations

from pathlib import Path
import plistlib


ROOT = Path(__file__).resolve().parents[1]

PLIST = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "com.aicontrolcenter.api.shadow.observer.plist"
)

RUNNER = (
    ROOT
    / "ops"
    / "macos"
    / "launchd"
    / "run-shadow-observer.sh"
)

OBSERVER = (
    ROOT
    / "ops"
    / "macos"
    / "monitoring"
    / "observe-shadow-daemon.py"
)

SUMMARY = (
    ROOT
    / "ops"
    / "macos"
    / "monitoring"
    / "summarize-shadow-observation.py"
)


def test_observer_files_exist() -> None:
    assert PLIST.is_file()
    assert RUNNER.is_file()
    assert OBSERVER.is_file()
    assert SUMMARY.is_file()


def test_observer_plist_contract() -> None:
    with PLIST.open("rb") as stream:
        payload = plistlib.load(stream)

    assert payload["Label"] == (
        "com.aicontrolcenter.api.shadow.observer"
    )

    assert payload["UserName"] == "kyouhan"
    assert payload["GroupName"] == "staff"
    assert payload["RunAtLoad"] is True
    assert payload["StartInterval"] == 300

    assert payload["ProgramArguments"] == [
        "/bin/bash",
        (
            "/usr/local/libexec/"
            "aicontrolcenter/"
            "run-shadow-observer.sh"
        ),
    ]

    assert payload["StandardOutPath"].startswith(
        "/var/log/aicontrolcenter/"
    )

    assert payload["StandardErrorPath"].startswith(
        "/var/log/aicontrolcenter/"
    )
