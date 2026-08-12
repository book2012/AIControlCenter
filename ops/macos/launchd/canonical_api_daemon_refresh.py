#!/usr/bin/env python3

"""Fail-closed refresh executor for installed canonical API assets."""

from __future__ import annotations

import argparse
import grp
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence

MODULE_DIRECTORY = Path(__file__).resolve().parent
if str(MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(MODULE_DIRECTORY))

from canonical_api_daemon import (  # noqa: E402
    INSTALLED_PLIST, INSTALLED_RUNNER, LABEL, SERVICE, canonical_paths,
    validate_contract,
)

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
RUNTIME_ID_RE = re.compile(r"^[0-9a-f]{12}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MARKER_NAME = ".aicontrolcenter-source-commit"
MANIFEST_NAME = ".aicontrolcenter-source-manifest.json"


def default_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def authorization_gate(*, apply: bool, confirmation: str, environment: Mapping[str, str], effective_user_id: int) -> dict[str, bool]:
    root = apply and effective_user_id == 0
    environment_authorized = apply and environment.get("AICONTROLCENTER_ALLOW_SYSTEM_WRITE") == "1"
    confirmed = apply and confirmation == LABEL
    return {
        "dry_run": not apply,
        "root_required": True,
        "root_verified": root,
        "environment_authorized": environment_authorized,
        "label_confirmed": confirmed,
        "apply_authorized": root and environment_authorized and confirmed,
    }


def _real_directory(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _regular_non_symlink(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _read_commit_marker(path: Path) -> str | None:
    if not _regular_non_symlink(path):
        return None
    try:
        value = path.read_text(encoding="ascii")
    except (OSError, UnicodeError):
        return None
    if not value.endswith("\n") or value.count("\n") != 1:
        return None
    commit = value[:-1]
    return commit if COMMIT_RE.fullmatch(commit) else None


def validate_immutable_source_context(root: Path) -> dict[str, Any]:
    source_root = Path(root)
    sources = source_root.parent
    runtime_root = sources.parent
    runtime_id = source_root.name
    venvs = runtime_root / "venvs"
    release = venvs / runtime_id
    source_marker = source_root / MARKER_NAME
    runtime_marker = release / MARKER_NAME
    manifest_path = source_root / MANIFEST_NAME

    checks: dict[str, bool] = {
        "source_root_real_directory": _real_directory(source_root),
        "runtime_id_valid": RUNTIME_ID_RE.fullmatch(runtime_id) is not None,
        "sources_real_directory": sources.name == "sources" and _real_directory(sources),
        "runtime_root_is_sources_parent": runtime_root == sources.parent,
        "venvs_real_directory": _real_directory(venvs),
        "runtime_release_real_directory": _real_directory(release),
        "source_marker_regular_file": _regular_non_symlink(source_marker),
        "runtime_marker_regular_file": _regular_non_symlink(runtime_marker),
        "source_manifest_regular_file": _regular_non_symlink(manifest_path),
    }
    try:
        physical_sources = sources.resolve(strict=True)
        physical_source = source_root.resolve(strict=True)
        checks["source_physical_direct_child"] = physical_source.parent == physical_sources
    except OSError:
        physical_source = source_root
        checks["source_physical_direct_child"] = False
    try:
        physical_venvs = venvs.resolve(strict=True)
        physical_release = release.resolve(strict=True)
        checks["runtime_release_physical_direct_child"] = physical_release.parent == physical_venvs
    except OSError:
        checks["runtime_release_physical_direct_child"] = False

    source_commit = _read_commit_marker(source_marker)
    runtime_commit = _read_commit_marker(runtime_marker)
    checks["source_commit_valid"] = source_commit is not None
    checks["runtime_commit_valid"] = runtime_commit is not None
    checks["source_runtime_commit_match"] = source_commit is not None and source_commit == runtime_commit

    manifest: Any = None
    if checks["source_manifest_regular_file"]:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
    required_fields = {
        "schema_version", "runtime_id", "source_commit", "git_tree",
        "archive_sha256", "content_sha256", "artifact_root", "build_status",
        "production_authorized",
    }
    checks["source_manifest_schema_valid"] = isinstance(manifest, dict) and set(manifest) == required_fields
    checks["source_manifest_identity_matches"] = bool(
        checks["source_manifest_schema_valid"]
        and manifest["schema_version"] == 1
        and manifest["runtime_id"] == runtime_id
        and source_commit is not None
        and manifest["source_commit"] == source_commit
        and manifest["artifact_root"] == str(physical_source)
        and manifest["build_status"] == "COMPLETE"
        and manifest["production_authorized"] is False
        and isinstance(manifest["git_tree"], str) and COMMIT_RE.fullmatch(manifest["git_tree"])
        and isinstance(manifest["archive_sha256"], str) and SHA256_RE.fullmatch(manifest["archive_sha256"])
        and isinstance(manifest["content_sha256"], str) and SHA256_RE.fullmatch(manifest["content_sha256"])
    )
    passed = all(checks.values())
    return {
        "validated": True, "immutable_source_context_valid": passed,
        "runtime_id": runtime_id, "source_commit": source_commit,
        "source_root": str(source_root), "runtime_root": str(runtime_root),
        "runtime_release": str(release), "checks": checks,
    }


def compile_commands(root: Path, installed_plist: Path, installed_runner: Path) -> list[dict[str, Any]]:
    source = canonical_paths(root.resolve())
    return [
        {"step": "refresh_runner", "argv": ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0755", str(source["runner"]), str(installed_runner)]},
        {"step": "refresh_plist", "argv": ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0644", str(source["plist"]), str(installed_plist)]},
    ]


def inspect_asset(path: Path, *, expected_uid: int, expected_gid: int, expected_mode: int) -> dict[str, Any]:
    inspection: dict[str, Any] = {
        "path": str(path), "exists": False, "regular_file": False, "symlink": False,
        "owner_matches": False, "group_matches": False, "mode_matches": False, "valid": False,
    }
    try:
        metadata = path.lstat()
    except OSError:
        return inspection
    inspection.update({
        "exists": True,
        "regular_file": stat.S_ISREG(metadata.st_mode),
        "symlink": stat.S_ISLNK(metadata.st_mode),
        "owner_matches": metadata.st_uid == expected_uid,
        "group_matches": metadata.st_gid == expected_gid,
        "mode_matches": stat.S_IMODE(metadata.st_mode) == expected_mode,
    })
    inspection["valid"] = all(inspection[key] for key in ("exists", "regular_file", "owner_matches", "group_matches", "mode_matches")) and not inspection["symlink"]
    return inspection


def execute(*, root: Path, apply: bool, confirmation: str = "", environment: Mapping[str, str] | None = None,
            effective_user_id: int | None = None, runner: CommandRunner = default_runner,
            installed_plist: Path = INSTALLED_PLIST, installed_runner: Path = INSTALLED_RUNNER,
            expected_uid: int = 0, expected_gid: int | None = None) -> dict[str, Any]:
    immutable_source = validate_immutable_source_context(root)
    contract = validate_contract(root.resolve())
    commands = compile_commands(root, installed_plist, installed_runner)
    authorization = authorization_gate(
        apply=apply, confirmation=confirmation,
        environment=os.environ if environment is None else environment,
        effective_user_id=os.geteuid() if effective_user_id is None else effective_user_id,
    )
    result: dict[str, Any] = {
        "schema_version": "1.0", "canonical_contract_gate_passed": contract["canonical_launchd_contract_gate_passed"],
        "canonical_refresh_gate_passed": False, "write_operations_executed": False,
        "authorization": authorization, "preflight_state": {"performed": False},
        "immutable_source": immutable_source, "commands": commands, "results": [],
        "service": SERVICE, "refresh_only": True,
    }
    if not apply:
        result["canonical_refresh_gate_passed"] = bool(
            immutable_source["immutable_source_context_valid"]
            and contract["canonical_launchd_contract_gate_passed"]
        )
        return result
    if not immutable_source["immutable_source_context_valid"]:
        result["failure"] = {"step": "immutable_source_context"}
        return result
    if not contract["canonical_launchd_contract_gate_passed"]:
        result["failure"] = {"step": "canonical_contract"}
        return result
    if not authorization["apply_authorized"]:
        result["failure"] = {"step": "system_write_authorization"}
        return result

    probe = runner(["/bin/launchctl", "print", SERVICE])
    result["preflight_state"] = {
        "performed": True, "service_probe_returncode": probe.returncode,
        "service_confirmed_absent": probe.returncode == 113,
    }
    if probe.returncode != 113:
        result["failure"] = {
            "step": "service_registration_probe", "returncode": probe.returncode,
            "detail": "Canonical service is registered" if probe.returncode == 0 else "Canonical service registration state is indeterminate",
        }
        return result

    wheel_gid = grp.getgrnam("wheel").gr_gid if expected_gid is None else expected_gid
    assets = {
        "plist": inspect_asset(installed_plist, expected_uid=expected_uid, expected_gid=wheel_gid, expected_mode=0o644),
        "runner": inspect_asset(installed_runner, expected_uid=expected_uid, expected_gid=wheel_gid, expected_mode=0o755),
    }
    result["preflight_state"]["installed_assets"] = assets
    invalid = [name for name, inspection in assets.items() if not inspection["valid"]]
    if invalid:
        result["failure"] = {"step": "installed_asset_validation", "invalid_assets": invalid}
        return result

    for index, command in enumerate(commands, start=1):
        completed = runner(command["argv"])
        result["results"].append({
            "index": index, "step": command["step"], "argv": command["argv"],
            "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr,
        })
        result["write_operations_executed"] = True
        if completed.returncode != 0:
            result["failure"] = {"step": command["step"], "returncode": completed.returncode, "stderr": completed.stderr}
            return result
    result["canonical_refresh_gate_passed"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("dry-run", "apply"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--confirm", default="")
    arguments = parser.parse_args()
    result = execute(root=arguments.root, apply=arguments.action == "apply", confirmation=arguments.confirm)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["canonical_refresh_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
