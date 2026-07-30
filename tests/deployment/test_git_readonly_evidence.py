from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.deployment.git_readonly_evidence import *


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ("/usr/bin/git", *args), cwd=cwd, check=True, shell=False,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/bin", "HOME": str(cwd), "LANG": "C", "LC_ALL": "C"})
    return result.stdout.decode().strip()


@pytest.fixture
def synchronized_repository(tmp_path):
    allowed = Path(os.environ["AICONTROLCENTER_GIT_EVIDENCE_TEST_ROOT"]).resolve()
    case = allowed / tmp_path.parent.name / tmp_path.name
    remote, repo = case / "remote.git", case / "repo"
    remote.parent.mkdir(parents=True)
    git(case, "init", "--bare", str(remote))
    git(case, "clone", str(remote), str(repo))
    git(repo, "checkout", "-b", "feature/deployment-package")
    (repo / "tracked.txt").write_text("baseline\n")
    git(repo, "add", "tracked.txt")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-m", "baseline")
    git(repo, "push", "-u", "origin", "feature/deployment-package")
    return repo


def config(repo: Path, **changes) -> ReadOnlyGitEvidenceConfig:
    values = {
        "repository_root": repo,
        "expected_branch": "feature/deployment-package",
        "expected_commit": git(repo, "rev-parse", "HEAD"),
    }
    values.update(changes)
    return ReadOnlyGitEvidenceConfig(**values)


def report(repo: Path, **changes):
    cfg = config(repo, **changes)
    snapshot = ReadOnlyGitEvidenceCollector(cfg).collect()
    return snapshot, ReadOnlyGitEvidenceValidator().validate(snapshot, cfg)


def codes(validation) -> set[str]:
    return {item.code for item in validation.findings}


def test_clean_synchronized_repository_accepted_and_digest_deterministic(
        synchronized_repository):
    first, validation = report(synchronized_repository)
    second = ReadOnlyGitEvidenceCollector(config(synchronized_repository)).collect()
    assert validation.status is ReadOnlyGitEvidenceStatus.COMPLETE
    assert first.evidence_digest == second.evidence_digest
    assert first.evidence_digest == canonical_digest(first.content())


@pytest.mark.parametrize(("prepare", "code"), [
    (lambda repo: (repo / "tracked.txt").write_text("dirty\n"), "UNSTAGED_CHANGES"),
    (lambda repo: ((repo / "tracked.txt").write_text("staged\n"),
                   git(repo, "add", "tracked.txt")), "STAGED_CHANGES"),
    (lambda repo: (repo / "untracked.txt").write_text("new\n"), "UNTRACKED_CHANGES"),
])
def test_dirty_states_rejected(synchronized_repository, prepare, code):
    prepare(synchronized_repository)
    _, validation = report(synchronized_repository)
    assert validation.status is ReadOnlyGitEvidenceStatus.BLOCKED
    assert code in codes(validation)


def test_branch_and_commit_mismatch_rejected(synchronized_repository):
    _, branch = report(synchronized_repository, expected_branch="other")
    _, commit = report(synchronized_repository, expected_commit="0" * 40)
    assert "BRANCH_MISMATCH" in codes(branch)
    assert "COMMIT_MISMATCH" in codes(commit)


def test_ahead_state_rejected(synchronized_repository):
    (synchronized_repository / "ahead.txt").write_text("ahead\n")
    git(synchronized_repository, "add", "ahead.txt")
    git(synchronized_repository, "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid", "commit", "-m", "ahead")
    _, validation = report(synchronized_repository)
    assert "AHEAD_OF_UPSTREAM" in codes(validation)


def test_behind_state_rejected(synchronized_repository):
    peer = synchronized_repository.parent / "peer"
    git(peer.parent, "clone", str(synchronized_repository.parent / "remote.git"), str(peer))
    git(peer, "checkout", "feature/deployment-package")
    (peer / "behind.txt").write_text("remote\n")
    git(peer, "add", "behind.txt")
    git(peer, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-m", "remote")
    git(peer, "push")
    git(synchronized_repository, "fetch", "origin")
    _, validation = report(synchronized_repository)
    assert "BEHIND_UPSTREAM" in codes(validation)


def test_missing_upstream_rejected(synchronized_repository):
    git(synchronized_repository, "branch", "--unset-upstream")
    with pytest.raises(ReadOnlyGitEvidenceError, match="GIT_COMMAND_FAILED"):
        ReadOnlyGitEvidenceCollector(config(synchronized_repository)).collect()


def fake_result(stdout=b"", stderr=b"", returncode=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def test_malformed_output_rejected(synchronized_repository):
    def runner(args, **kwargs):
        if args[1:] == ("rev-parse", "--show-toplevel"):
            return fake_result(b"bad\nroot\n")
        return fake_result()
    with pytest.raises(ReadOnlyGitEvidenceError, match="GIT_OUTPUT_MALFORMED"):
        ReadOnlyGitEvidenceCollector(config(synchronized_repository), runner=runner).collect()


def test_timeout_rejected(synchronized_repository):
    def runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1)
    with pytest.raises(ReadOnlyGitEvidenceError, match="GIT_COMMAND_TIMEOUT"):
        ReadOnlyGitEvidenceCollector(config(synchronized_repository), runner=runner).collect()


def test_executable_commands_and_shell_are_closed(synchronized_repository):
    with pytest.raises(ReadOnlyGitEvidenceError):
        config(synchronized_repository, executable=Path("/bin/git"))
    assert set(ReadOnlyGitEvidenceCommand) == {
        ReadOnlyGitEvidenceCommand.SHOW_TOPLEVEL,
        ReadOnlyGitEvidenceCommand.SHOW_BRANCH,
        ReadOnlyGitEvidenceCommand.SHOW_HEAD,
        ReadOnlyGitEvidenceCommand.SHOW_STATUS,
        ReadOnlyGitEvidenceCommand.SHOW_UPSTREAM,
        ReadOnlyGitEvidenceCommand.SHOW_PARITY,
    }
    calls = []
    def runner(args, **kwargs):
        calls.append((args, kwargs))
        raise subprocess.TimeoutExpired(args, 1)
    with pytest.raises(ReadOnlyGitEvidenceError):
        ReadOnlyGitEvidenceCollector(config(synchronized_repository), runner=runner).collect()
    args, kwargs = calls[0]
    assert args[0] == "/usr/bin/git"
    assert kwargs["shell"] is False
    forbidden = {"add", "commit", "checkout", "reset", "clean", "stash",
                 "fetch", "pull", "push", "config"}
    assert forbidden.isdisjoint(args)
