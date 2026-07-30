"""Immutable contracts for bounded, read-only Git evidence."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class ReadOnlyGitEvidenceError(RuntimeError):
    pass


class ReadOnlyGitEvidenceCommand(StrEnum):
    SHOW_TOPLEVEL = "SHOW_TOPLEVEL"
    SHOW_BRANCH = "SHOW_BRANCH"
    SHOW_HEAD = "SHOW_HEAD"
    SHOW_STATUS = "SHOW_STATUS"
    SHOW_UPSTREAM = "SHOW_UPSTREAM"
    SHOW_PARITY = "SHOW_PARITY"


class ReadOnlyGitEvidenceStatus(StrEnum):
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"


_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_UPSTREAM = re.compile(r"^refs/remotes/[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")


def canonical_json(value: Any) -> str:
    if isinstance(value, Path):
        value = str(value)
    elif isinstance(value, StrEnum):
        value = value.value
    elif isinstance(value, dict):
        value = {str(key): value[key] for key in sorted(value)}
    elif isinstance(value, (tuple, list)):
        value = [item.value if isinstance(item, StrEnum) else item for item in value]
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ReadOnlyGitEvidenceConfig:
    repository_root: Path
    expected_branch: str
    expected_commit: str
    executable: Path = Path("/usr/bin/git")
    timeout_seconds: float = 5.0
    maximum_output_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        supplied = Path(self.repository_root)
        if (not supplied.is_absolute() or supplied.is_symlink()
                or any(parent.is_symlink() for parent in supplied.parents)
                or supplied != supplied.resolve()
                or Path(self.executable) != Path("/usr/bin/git")
                or not _BRANCH.fullmatch(self.expected_branch)
                or not _COMMIT.fullmatch(self.expected_commit)
                or not 0 < self.timeout_seconds <= 10
                or not 1 <= self.maximum_output_bytes <= 4_194_304):
            raise ReadOnlyGitEvidenceError("GIT_EVIDENCE_CONFIG_REJECTED")
        object.__setattr__(self, "repository_root", supplied)
        object.__setattr__(self, "executable", Path("/usr/bin/git"))


@dataclass(frozen=True, slots=True, order=True)
class ReadOnlyGitEvidenceFinding:
    code: str


@dataclass(frozen=True, slots=True)
class ReadOnlyGitEvidenceSnapshot:
    repository_root: Path
    branch: str
    head: str
    expected_branch: str
    expected_commit: str
    working_tree_clean: bool
    staged_count: int
    unstaged_count: int
    untracked_count: int
    upstream: str | None
    ahead: int | None
    behind: int | None
    collection_status: ReadOnlyGitEvidenceStatus
    evidence_digest: str

    def content(self) -> dict[str, Any]:
        value = asdict(self)
        value["repository_root"] = str(self.repository_root)
        value["collection_status"] = self.collection_status.value
        value.pop("evidence_digest")
        return value

    def as_dict(self) -> dict[str, Any]:
        return {**self.content(), "evidence_digest": self.evidence_digest}

    @classmethod
    def build(cls, **values: Any) -> "ReadOnlyGitEvidenceSnapshot":
        content = dict(values)
        content["repository_root"] = str(content["repository_root"])
        content["collection_status"] = content["collection_status"].value
        digest = canonical_digest(content)
        content["repository_root"] = Path(content["repository_root"])
        content["collection_status"] = ReadOnlyGitEvidenceStatus(
            content["collection_status"])
        return cls(**content, evidence_digest=digest)


@dataclass(frozen=True, slots=True)
class ReadOnlyGitEvidenceValidationReport:
    status: ReadOnlyGitEvidenceStatus
    findings: tuple[ReadOnlyGitEvidenceFinding, ...]
    evidence_digest: str
