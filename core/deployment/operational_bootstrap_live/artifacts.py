"""Strict canonical readers and atomic writers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

from .models import ControlledOperationalBootstrapError, canonical_json, validate_safe


class StrictControlledOperationalArtifactReader:
    def read(self, path: Path) -> Mapping[str, object]:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
        if not isinstance(value, dict) or canonical_json(value) != raw:
            raise ControlledOperationalBootstrapError("STRICT_CANONICAL_JSON_REQUIRED")
        validate_safe(value)
        return value


class StrictControlledOperationalPreflightArtifactReader:
    """Strict reader for the one contract containing Ubuntu deny-evidence."""

    def read(self, path: Path) -> Mapping[str, object]:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
        if not isinstance(value, dict) or canonical_json(value) != raw:
            raise ControlledOperationalBootstrapError("STRICT_CANONICAL_JSON_REQUIRED")
        expected = {
            "status", "branch", "commit", "trusted_operational_root",
            "managed_targets_absent", "shared_parent_digest",
            "ubuntu_participation"}
        if set(value) != expected:
            unknown = set(value) - expected
            if unknown:
                validate_safe({name: value[name] for name in unknown})
            raise ControlledOperationalBootstrapError("ARTIFACT_FIELDS_INVALID")
        if ("ubuntu_participation" not in value
                or type(value["ubuntu_participation"]) is not bool
                or value["ubuntu_participation"] is not False):
            raise ControlledOperationalBootstrapError(
                "UBUNTU_PARTICIPATION_MUST_BE_FALSE")
        remaining = dict(value)
        remaining.pop("ubuntu_participation")
        trusted_root = remaining.pop("trusted_operational_root")
        validate_safe(remaining)
        if not isinstance(trusted_root, str) or "://" in trusted_root:
            raise ControlledOperationalBootstrapError("UNSAFE_VALUE_REJECTED")
        return value


class AtomicControlledOperationalArtifactWriter:
    def write(self, path: Path, value: Mapping[str, object]) -> None:
        path = Path(path)
        if path.exists() or path.is_symlink() or path.parent.is_symlink():
            raise ControlledOperationalBootstrapError("ARTIFACT_ALREADY_EXISTS")
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = path.with_name("." + path.name + ".incomplete")
        if temporary.exists() or temporary.is_symlink():
            raise ControlledOperationalBootstrapError("INCOMPLETE_ARTIFACT_EXISTS")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(descriptor, canonical_json(value).encode())
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
