"""Read-only macOS SOPS/age backend metadata adapter."""

from __future__ import annotations

import json
import re
import stat
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from core.secrets.ports import SecretBackendInspection

ROOT = Path(__file__).resolve().parents[3]
DEFINITION_PATH = ROOT / "config/shopping-secret-backend.json"
REQUIRED_EXECUTABLES = ("sops", "age", "age-keygen")
PAYLOAD_PATH_PATTERN = re.compile(
    r"^deploy/shopping/secrets/[a-z0-9.-]+\.enc\.yaml$"
)


class BackendDefinitionError(ValueError):
    """The canonical backend definition is malformed."""


def load_definition(path: Path = DEFINITION_PATH) -> dict[str, Any]:
    definition = json.loads(path.read_text(encoding="utf-8"))
    validate_definition(definition)
    return definition


def validate_definition(definition: object) -> None:
    if not isinstance(definition, dict) or set(definition) != {
        "schema_version", "definition_id", "owner", "backend_kind",
        "production_status", "value_free", "materialization_implemented",
        "encrypted_payload", "identity_custody", "control_plane_recipient",
        "offline_recovery_inbox", "offline_recovery_recipient", "recipient_policy",
    }:
        raise BackendDefinitionError("definition fields do not match schema v1")
    expected = {
        "schema_version": "1.0", "definition_id": "shopping-secret-backend",
        "owner": "MAC_MINI_M4_AICONTROLCENTER_CONTROL_PLANE",
        "backend_kind": "sops-age", "production_status": "NOT_DEPLOYED",
        "value_free": True, "materialization_implemented": False,
    }
    if any(definition[key] != value for key, value in expected.items()):
        raise BackendDefinitionError("definition identity or safety metadata is invalid")
    payload = definition["encrypted_payload"]
    custody = definition["identity_custody"]
    policy = definition["recipient_policy"]
    if not isinstance(payload, dict) or set(payload) != {"path", "required_owner", "maximum_mode"}:
        raise BackendDefinitionError("encrypted payload contract is invalid")
    payload_path = payload.get("path")
    if (
        not isinstance(payload_path, str)
        or Path(payload_path).is_absolute()
        or ".." in Path(payload_path).parts
        or PAYLOAD_PATH_PATTERN.fullmatch(payload_path) is None
    ):
        raise BackendDefinitionError("encrypted payload path is outside the allowed namespace")
    if payload.get("required_owner") != "control-plane-user" or payload.get("maximum_mode") != "0600":
        raise BackendDefinitionError("encrypted payload metadata policy is invalid")
    if not isinstance(custody, dict) or set(custody) != {"platform", "base", "relative_path", "required_owner", "maximum_mode", "external_to_repository", "contents_inspected"}:
        raise BackendDefinitionError("identity custody contract is invalid")
    relative_path = custody.get("relative_path")
    if (custody.get("platform"), custody.get("base"), custody.get("required_owner"), custody.get("maximum_mode"), custody.get("external_to_repository"), custody.get("contents_inspected")) != ("macos", "control-plane-home", "control-plane-user", "0600", True, False):
        raise BackendDefinitionError("identity custody policy is invalid")
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or Path(relative_path).is_absolute()
        or ".." in Path(relative_path).parts
        or relative_path != ".config/sops/age/keys.txt"
    ):
        raise BackendDefinitionError("identity relative path is invalid")
    if not isinstance(policy, dict) or policy != {"minimum_recipients": 2, "roles": ["control-plane", "offline-recovery"], "recipient_material_stored": False}:
        raise BackendDefinitionError("recipient policy is invalid")
    portable_paths = {
        "control_plane_recipient": (".config/aicontrolcenter/shopping-secrets/recipients/control-plane.txt", False),
        "offline_recovery_inbox": (".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt", True),
        "offline_recovery_recipient": (".config/aicontrolcenter/shopping-secrets/recipients/offline-recovery.txt", False),
    }
    for key, (expected_path, has_external_custody) in portable_paths.items():
        metadata = definition[key]
        expected_keys = {"base", "relative_path", "required_owner", "maximum_mode"}
        if has_external_custody:
            expected_keys.add("private_identity_custody")
        if not isinstance(metadata, dict) or set(metadata) != expected_keys:
            raise BackendDefinitionError("portable recipient metadata is invalid")
        if (metadata.get("base"), metadata.get("relative_path"), metadata.get("required_owner"), metadata.get("maximum_mode")) != ("control-plane-home", expected_path, "control-plane-user", "0600"):
            raise BackendDefinitionError("portable recipient path policy is invalid")
        path = Path(metadata["relative_path"])
        if path.is_absolute() or ".." in path.parts:
            raise BackendDefinitionError("portable recipient path is invalid")
        if has_external_custody and metadata.get("private_identity_custody") != "external":
            raise BackendDefinitionError("offline recovery private custody is invalid")


def _safe_file(path: Path, expected_uid: int, maximum_mode: int) -> tuple[bool, bool, bool]:
    try:
        metadata = path.lstat()
    except OSError:
        return False, False, False
    present = stat.S_ISREG(metadata.st_mode)
    owner_safe = present and metadata.st_uid == expected_uid
    mode_safe = present and stat.S_IMODE(metadata.st_mode) & ~maximum_mode == 0
    return present, owner_safe, mode_safe


class SopsAgeBackendAdapter:
    def __init__(
        self,
        definition: Mapping[str, Any],
        *,
        executable_resolver: Callable[[str], str | None],
        control_plane_home: Path,
        repository_root: Path = ROOT,
        expected_uid: int,
    ) -> None:
        self._definition = dict(definition)
        self._resolver = executable_resolver
        self._root = repository_root
        self._control_plane_home = control_plane_home
        if not isinstance(expected_uid, int) or isinstance(expected_uid, bool) or expected_uid < 0:
            raise ValueError("INVALID_EXPECTED_UID")
        self._expected_uid = expected_uid

    def inspect(self) -> SecretBackendInspection:
        try:
            validate_definition(self._definition)
        except BackendDefinitionError:
            return SecretBackendInspection("unknown", "UNKNOWN", False, False, (), "MALFORMED_CONFIGURATION")
        checks = [(f"executable:{name}", bool(self._resolver(name))) for name in REQUIRED_EXECUTABLES]
        payload = self._definition["encrypted_payload"]
        custody = self._definition["identity_custody"]
        payload_checks = _safe_file(self._root / payload["path"], self._expected_uid, int(payload["maximum_mode"], 8))
        identity_path = self._control_plane_home / custody["relative_path"]
        identity_checks = _safe_file(identity_path, self._expected_uid, int(custody["maximum_mode"], 8))
        for prefix, results in (("payload", payload_checks), ("identity", identity_checks)):
            checks.extend((f"{prefix}:{name}", passed) for name, passed in zip(("present", "owner", "mode"), results))
        ready = all(passed for _, passed in checks)
        return SecretBackendInspection("sops-age", "NOT_DEPLOYED", True, ready, tuple(checks))


__all__ = ("BackendDefinitionError", "SopsAgeBackendAdapter", "load_definition", "validate_definition")
