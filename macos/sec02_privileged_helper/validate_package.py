#!/usr/bin/env python3
"""Render and validate the fixed, non-Production SEC-02 app bundle."""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT / "package-contract.json"
TEMPLATES = ROOT / "templates"
EXPECTED = {
    "app_bundle_identifier": "com.aicontrolcenter.app",
    "helper_bundle_identifier": "com.aicontrolcenter.sec02-remediation-helper",
    "mach_service_identifier": "com.aicontrolcenter.sec02-remediation-helper",
    "launchdaemon_plist_name": "com.aicontrolcenter.sec02-remediation-helper.plist",
}
APP_EXECUTABLE = "AIControlCenter"
HELPER_EXECUTABLE = "SEC02GovernanceRemediationHelper"


class PackageContractError(ValueError):
    pass


def load_contract() -> dict:
    value = json.loads(CONTRACT.read_text())
    for key, expected in EXPECTED.items():
        if value.get(key) != expected:
            raise PackageContractError(f"{key} is not the frozen value")
    if value.get("executables") != {"app": APP_EXECUTABLE, "helper": HELPER_EXECUTABLE}:
        raise PackageContractError("executable names are not frozen")
    return value


def validate_templates() -> None:
    raw = b"\n".join(path.read_bytes() for path in sorted(TEMPLATES.iterdir()))
    if b"${" in raw:
        raise PackageContractError("unresolved template placeholder")
    app = plistlib.loads((TEMPLATES / "App-Info.plist").read_bytes())
    helper = plistlib.loads((TEMPLATES / "Helper-Info.plist").read_bytes())
    daemon = plistlib.loads((TEMPLATES / "LaunchDaemon.plist").read_bytes())
    if app != {"CFBundleExecutable": APP_EXECUTABLE,
               "CFBundleIdentifier": EXPECTED["app_bundle_identifier"],
               "CFBundlePackageType": "APPL"}:
        raise PackageContractError("invalid app plist")
    if helper.get("CFBundleExecutable") != HELPER_EXECUTABLE or helper.get("CFBundleIdentifier") != EXPECTED["helper_bundle_identifier"]:
        raise PackageContractError("invalid helper plist")
    if daemon != {"Label": EXPECTED["helper_bundle_identifier"],
                  "BundleProgram": f"Contents/MacOS/{HELPER_EXECUTABLE}",
                  "MachServices": {EXPECTED["mach_service_identifier"]: True}}:
        raise PackageContractError("invalid LaunchDaemon plist")


def build(destination: Path) -> Path:
    load_contract()
    validate_templates()
    if not destination.is_absolute() or destination.name != "AIControlCenter.app":
        raise PackageContractError("destination must be an absolute AIControlCenter.app path")
    contents = destination / "Contents"
    macos = contents / "MacOS"
    daemons = contents / "Library" / "LaunchDaemons"
    destination.mkdir(parents=True, exist_ok=False)
    macos.mkdir(parents=True)
    daemons.mkdir(parents=True)
    shutil.copyfile(TEMPLATES / "App-Info.plist", contents / "Info.plist")
    shutil.copyfile(TEMPLATES / "LaunchDaemon.plist", daemons / EXPECTED["launchdaemon_plist_name"])
    for executable in (APP_EXECUTABLE, HELPER_EXECUTABLE):
        (macos / executable).touch(mode=0o755)
    validate_bundle(destination)
    return destination


def validate_bundle(bundle: Path) -> None:
    expected = {
        "Contents/Info.plist", f"Contents/MacOS/{APP_EXECUTABLE}",
        f"Contents/MacOS/{HELPER_EXECUTABLE}",
        f"Contents/Library/LaunchDaemons/{EXPECTED['launchdaemon_plist_name']}",
    }
    actual = {str(path.relative_to(bundle)) for path in bundle.rglob("*") if path.is_file()}
    if actual != expected:
        raise PackageContractError("bundle layout mismatch")
    validate_templates()


def signing_readiness(team_id: str | None, app_requirement: str | None,
                      helper_requirement: str | None) -> bool:
    """Raw strings never confer trust; native resolver output is mandatory."""
    del team_id, app_requirement, helper_requirement
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=Path)
    args = parser.parse_args()
    load_contract()
    validate_templates()
    if args.build:
        build(args.build)
    print("TEMPORARY_PACKAGE_LAYOUT_VALIDATED=YES")
    print("LIVE_SIGNING_READINESS=NOT_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
