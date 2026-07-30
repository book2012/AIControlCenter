"""The sole approved subprocess adapter for deployment-control Git evidence."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .models import *

_UPSTREAM = re.compile(r"^(?:refs/remotes/)?[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


_FIXED = {
    ReadOnlyGitEvidenceCommand.SHOW_TOPLEVEL:
        ("/usr/bin/git", "rev-parse", "--show-toplevel"),
    ReadOnlyGitEvidenceCommand.SHOW_BRANCH:
        ("/usr/bin/git", "branch", "--show-current"),
    ReadOnlyGitEvidenceCommand.SHOW_HEAD:
        ("/usr/bin/git", "rev-parse", "HEAD"),
    ReadOnlyGitEvidenceCommand.SHOW_STATUS:
        ("/usr/bin/git", "status", "--porcelain=v2", "-z", "--untracked-files=all"),
    ReadOnlyGitEvidenceCommand.SHOW_UPSTREAM:
        ("/usr/bin/git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"),
}


class ReadOnlyGitEvidenceCollector:
    def __init__(self, config: ReadOnlyGitEvidenceConfig, *, runner=subprocess.run) -> None:
        self.config = config
        self._runner = runner

    def _run(self, command: ReadOnlyGitEvidenceCommand,
             upstream: str | None = None) -> bytes:
        if command is ReadOnlyGitEvidenceCommand.SHOW_PARITY:
            if upstream is None or not _UPSTREAM.fullmatch(upstream):
                raise ReadOnlyGitEvidenceError("GIT_UPSTREAM_MALFORMED")
            args = ("/usr/bin/git", "rev-list", "--left-right", "--count",
                    f"HEAD...{upstream}")
        else:
            try:
                args = _FIXED[command]
            except (KeyError, TypeError) as exc:
                raise ReadOnlyGitEvidenceError("GIT_COMMAND_REJECTED") from exc
        try:
            result = self._runner(
                args, cwd=self.config.repository_root, shell=False,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=self.config.timeout_seconds,
                check=False, env={"PATH": "/usr/bin:/bin", "LANG": "C",
                                  "LC_ALL": "C", "HOME": "/nonexistent",
                                  "GIT_CONFIG_NOSYSTEM": "1",
                                  "GIT_TERMINAL_PROMPT": "0"})
        except subprocess.TimeoutExpired as exc:
            raise ReadOnlyGitEvidenceError("GIT_COMMAND_TIMEOUT") from exc
        if not isinstance(result.stdout, bytes) or not isinstance(result.stderr, bytes):
            raise ReadOnlyGitEvidenceError("GIT_OUTPUT_MALFORMED")
        if (len(result.stdout) > self.config.maximum_output_bytes
                or len(result.stderr) > self.config.maximum_output_bytes):
            raise ReadOnlyGitEvidenceError("GIT_OUTPUT_TOO_LARGE")
        if result.returncode:
            raise ReadOnlyGitEvidenceError("GIT_COMMAND_FAILED")
        return result.stdout

    @staticmethod
    def _line(raw: bytes) -> str:
        try:
            value = raw.decode("utf-8").rstrip("\n")
        except UnicodeDecodeError as exc:
            raise ReadOnlyGitEvidenceError("GIT_OUTPUT_MALFORMED") from exc
        if not value or "\n" in value or "\x00" in value:
            raise ReadOnlyGitEvidenceError("GIT_OUTPUT_MALFORMED")
        return value

    @staticmethod
    def _status(raw: bytes) -> tuple[int, int, int]:
        staged = unstaged = untracked = 0
        for record in raw.split(b"\0"):
            if not record:
                continue
            try:
                text = record.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ReadOnlyGitEvidenceError("GIT_STATUS_MALFORMED") from exc
            if text.startswith("? "):
                untracked += 1
            elif text.startswith("! "):
                continue
            elif text[:2] in {"1 ", "2 ", "u "} and len(text.split(" ", 3)[1]) == 2:
                xy = text.split(" ", 3)[1]
                staged += xy[0] != "."
                unstaged += xy[1] != "."
            else:
                raise ReadOnlyGitEvidenceError("GIT_STATUS_MALFORMED")
        return staged, unstaged, untracked

    def collect(self) -> ReadOnlyGitEvidenceSnapshot:
        root = Path(self._line(self._run(
            ReadOnlyGitEvidenceCommand.SHOW_TOPLEVEL)))
        branch = self._line(self._run(ReadOnlyGitEvidenceCommand.SHOW_BRANCH))
        head = self._line(self._run(ReadOnlyGitEvidenceCommand.SHOW_HEAD))
        staged, unstaged, untracked = self._status(
            self._run(ReadOnlyGitEvidenceCommand.SHOW_STATUS))
        upstream = self._line(self._run(ReadOnlyGitEvidenceCommand.SHOW_UPSTREAM))
        if not _UPSTREAM.fullmatch(upstream):
            raise ReadOnlyGitEvidenceError("GIT_UPSTREAM_MALFORMED")
        parity = self._line(self._run(
            ReadOnlyGitEvidenceCommand.SHOW_PARITY, upstream)).split()
        if len(parity) != 2 or any(not item.isdecimal() for item in parity):
            raise ReadOnlyGitEvidenceError("GIT_PARITY_MALFORMED")
        ahead, behind = map(int, parity)
        if root != self.config.repository_root or not _BRANCH.fullmatch(branch) or not _COMMIT.fullmatch(head):
            raise ReadOnlyGitEvidenceError("GIT_IDENTITY_MALFORMED")
        return ReadOnlyGitEvidenceSnapshot.build(
            repository_root=root, branch=branch, head=head,
            expected_branch=self.config.expected_branch,
            expected_commit=self.config.expected_commit,
            working_tree_clean=not (staged or unstaged or untracked),
            staged_count=staged, unstaged_count=unstaged,
            untracked_count=untracked, upstream=upstream, ahead=ahead,
            behind=behind, collection_status=ReadOnlyGitEvidenceStatus.COMPLETE)


class ReadOnlyGitEvidenceValidator:
    def validate(self, snapshot: ReadOnlyGitEvidenceSnapshot,
                 config: ReadOnlyGitEvidenceConfig) -> ReadOnlyGitEvidenceValidationReport:
        findings = []
        checks = (
            ("REPOSITORY_ROOT_MISMATCH", snapshot.repository_root != config.repository_root),
            ("BRANCH_MISMATCH", snapshot.branch != config.expected_branch),
            ("COMMIT_MISMATCH", snapshot.head != config.expected_commit),
            ("WORKING_TREE_DIRTY", not snapshot.working_tree_clean),
            ("STAGED_CHANGES", snapshot.staged_count != 0),
            ("UNSTAGED_CHANGES", snapshot.unstaged_count != 0),
            ("UNTRACKED_CHANGES", snapshot.untracked_count != 0),
            ("UPSTREAM_MISSING", snapshot.upstream is None),
            ("AHEAD_OF_UPSTREAM", snapshot.ahead != 0),
            ("BEHIND_UPSTREAM", snapshot.behind != 0),
            ("EVIDENCE_DIGEST_INVALID",
             snapshot.evidence_digest != canonical_digest(snapshot.content())),
        )
        findings.extend(ReadOnlyGitEvidenceFinding(code) for code, failed in checks if failed)
        status = (ReadOnlyGitEvidenceStatus.BLOCKED if findings
                  else ReadOnlyGitEvidenceStatus.COMPLETE)
        return ReadOnlyGitEvidenceValidationReport(
            status, tuple(sorted(findings)), snapshot.evidence_digest)
