from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

def default_runtime_metadata_path() -> Path:
    configured = os.getenv(
        "AICONTROLCENTER_RUNTIME_METADATA"
    )
    if configured:
        return Path(configured).expanduser()

    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "AIControlCenter"
        / "runtime"
        / "current"
        / "metadata.json"
    )

class RuntimeMetadata:
    SUPPORTED_SCHEMA_VERSION = 1
    SUPPORTED_RUNTIME_MODES = {"shadow"}
    COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:
        self.path = (
            Path(path).expanduser()
            if path is not None
            else default_runtime_metadata_path()
        )

    def _unavailable(
        self,
        error_type: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "available": False,
            "schema_version": None,
            "commit": None,
            "short_commit": None,
            "runtime_mode": None,
            "created_at": None,
            "metadata_path": str(self.path),
            "error": {
                "type": error_type,
                "message": message,
            },
        }

    def _validate(self, data: dict[str, Any]) -> str | None:
        required_fields = (
            "schema_version",
            "commit",
            "short_commit",
            "runtime_mode",
            "created_at",
        )
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"

        if data["schema_version"] != self.SUPPORTED_SCHEMA_VERSION:
            return "Unsupported schema_version"

        commit = data["commit"]
        if (
            not isinstance(commit, str)
            or self.COMMIT_PATTERN.fullmatch(commit) is None
        ):
            return "Invalid commit format"

        short_commit = data["short_commit"]
        if (
            not isinstance(short_commit, str)
            or short_commit != commit[:12]
        ):
            return "Invalid short_commit"

        runtime_mode = data["runtime_mode"]
        if runtime_mode not in self.SUPPORTED_RUNTIME_MODES:
            return "Invalid runtime_mode"

        created_at = data["created_at"]
        if (
            not isinstance(created_at, str)
            or not created_at.strip()
        ):
            return "Invalid created_at"

        return None

    def status(self) -> dict[str, Any]:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self._unavailable(
                "metadata_not_found",
                "Runtime metadata file was not found.",
            )
        except OSError as exc:
            return self._unavailable(
                "metadata_read_error",
                str(exc),
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return self._unavailable(
                "invalid_metadata_json",
                str(exc),
            )

        if not isinstance(data, dict):
            return self._unavailable(
                "invalid_metadata_shape",
                "Runtime metadata must be a JSON object.",
            )

        validation_error = self._validate(data)
        if validation_error is not None:
            return self._unavailable(
                "invalid_metadata_schema",
                validation_error,
            )

        return {
            "available": True,
            "schema_version": data.get("schema_version"),
            "commit": data.get("commit"),
            "short_commit": data.get("short_commit"),
            "runtime_mode": data.get("runtime_mode"),
            "created_at": data.get("created_at"),
            "metadata_path": str(self.path),
            "error": None,
        }
