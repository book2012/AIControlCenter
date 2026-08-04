from __future__ import annotations

import json
import os
import re
import tempfile
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
        serialized = json.dumps(
            self.payload(),
            indent=2,
            sort_keys=True,
        ) + "\n"
        marker = f"{self.commit}\n"

        runtime_dir = Path(self.runtime_dir).expanduser()
        runtime_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = runtime_dir / "metadata.json"
        marker_path = runtime_dir / ".aicontrolcenter-source-commit"
        if metadata_path.exists() or marker_path.exists():
            raise FileExistsError(
                "Runtime metadata contract already exists"
            )

        temporary_paths: list[Path] = []
        published_paths: list[Path] = []

        def stage(prefix: str, content: str) -> Path:
            descriptor, name = tempfile.mkstemp(
                prefix=prefix,
                suffix=".tmp",
                dir=runtime_dir,
                text=True,
            )
            path = Path(name)
            temporary_paths.append(path)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            return path

        try:
            temporary_metadata = stage(".metadata.json.", serialized)
            temporary_marker = stage(
                ".aicontrolcenter-source-commit.",
                marker,
            )

            os.replace(temporary_marker, marker_path)
            temporary_paths.remove(temporary_marker)
            published_paths.append(marker_path)

            os.replace(temporary_metadata, metadata_path)
            temporary_paths.remove(temporary_metadata)
            published_paths.append(metadata_path)

            marker_path.chmod(0o444)
            metadata_path.chmod(0o444)
        except BaseException:
            for path in reversed(published_paths):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise
        finally:
            for path in temporary_paths:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass

        return metadata_path
