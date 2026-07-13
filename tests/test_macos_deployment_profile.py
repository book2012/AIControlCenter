from __future__ import annotations

import plistlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MACOS_ROOT = PROJECT_ROOT / "deploy" / "macos"


def test_macos_deployment_files_exist() -> None:
    expected = [
        MACOS_ROOT / "bootstrap-macos.sh",
        MACOS_ROOT / "install-launchd.sh",
        MACOS_ROOT / "uninstall-launchd.sh",
        MACOS_ROOT / "validate-macos-profile.sh",
        MACOS_ROOT / "com.aihome.aicontrolcenter.plist",
        PROJECT_ROOT / "config" / "workers.mac-production.yaml",
        PROJECT_ROOT / ".env.mac-production.example",
    ]

    missing = [
        str(path.relative_to(PROJECT_ROOT))
        for path in expected
        if not path.exists()
    ]

    assert missing == []


def test_launchd_profile_is_valid_plist() -> None:
    path = (
        MACOS_ROOT
        / "com.aihome.aicontrolcenter.plist"
    )

    with path.open("rb") as file:
        profile = plistlib.load(file)

    assert profile["Label"] == (
        "com.aihome.aicontrolcenter"
    )
    assert profile["RunAtLoad"] is True
    assert profile["WorkingDirectory"] == (
        "/opt/AIControlCenter"
    )


def test_bootstrap_does_not_install_launchd_automatically() -> None:
    content = (
        MACOS_ROOT
        / "bootstrap-macos.sh"
    ).read_text(encoding="utf-8")

    assert "launchctl bootstrap" not in content
    assert "install-launchd.sh" not in content


def test_environment_template_contains_datacenter_settings() -> None:
    content = (
        PROJECT_ROOT
        / ".env.mac-production.example"
    ).read_text(encoding="utf-8")

    required = [
        "DATACENTER_HOST=",
        "DATACENTER_SSH_USER=",
        "DATACENTER_SSH_PORT=",
        "DATACENTER_MAC_ADDRESS=",
        "DATACENTER_WOL_BROADCAST=",
    ]

    for setting in required:
        assert setting in content
