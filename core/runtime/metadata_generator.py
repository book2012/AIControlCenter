from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

@dataclass(frozen=True)
class RuntimeMetadataGenerator:
    runtime_dir: Path
    commit: str
    short_commit: str
    runtime_mode: str = "shadow"
    created_at: str | None = None

    SCHEMA_VERSION = 1
    COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
    SUPPORTED_RUNTIME_MODES = {"shadow"}

    def _validate(self) -> None:
        if self.COMMIT_PATTERN.fullmatch(self.commit) is None:
            raise ValueError("Invalid commit format")

        if self.short_commit != self.commit[:12]:
            raise ValueError("Invalid short_commit")

        if self.runtime_mode not in self.SUPPORTED_RUNTIME_MODES:
            raise ValueError("Invalid runtime_mode")

        if self.created_at is not None and not self.created_at.strip():
            raise ValueError("Invalid created_at")

    def payload(self) -> dict:
        self._validate()
        created_at = self.created_at or (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        return {
            "schema_version": self.SCHEMA_VERSION,
            "commit": self.commit,
            "short_commit": self.short_commit,
            "runtime_mode": self.runtime_mode,
            "created_at": created_at,
        }

    def write(self) -> Path:
        runtime_dir = Path(self.runtime_dir).expanduser()
        runtime_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = runtime_dir / "metadata.json"
        temporary_path = runtime_dir / ".metadata.json.tmp"
        serialized = json.dumps(
            self.payload(),
            indent=2,
            sort_keys=True,
        ) + "\n"

        temporary_path.write_text(
            serialized,
            encoding="utf-8",
        )
        temporary_path.replace(metadata_path)
        metadata_path.chmod(0o444)

        return metadata_path
