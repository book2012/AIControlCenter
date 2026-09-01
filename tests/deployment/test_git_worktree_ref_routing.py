from pathlib import Path

import pytest

from core.deployment.adapters.macos.repository import (
    GitRepositoryAdapter,
    RepositoryFileReader,
)

COMMIT_A = "a" * 40
COMMIT_B = "b" * 40


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _linked_repository(tmp_path: Path) -> tuple[Path, Path]:
    common_dir = tmp_path / "common.git"
    git_dir = common_dir / "worktrees" / "ops-val"
    git_dir.mkdir(parents=True)
    _write(tmp_path / ".git", f"gitdir: {git_dir}\n")
    _write(git_dir / "commondir", "../..\n")
    _write(git_dir / "gitdir", f"{tmp_path / '.git'}\n")
    _write(git_dir / "HEAD", "ref: refs/heads/feature\n")
    return common_dir, git_dir


def _observe(tmp_path: Path) -> dict[str, object]:
    return GitRepositoryAdapter(
        RepositoryFileReader(tmp_path)
    ).observe_git_identity()


def test_linked_worktree_shared_ref_ignores_private_shadow(
    tmp_path: Path,
) -> None:
    common_dir, git_dir = _linked_repository(tmp_path)
    _write(common_dir / "refs/heads/feature", f"{COMMIT_A}\n")
    _write(git_dir / "refs/heads/feature", f"{COMMIT_B}\n")

    observed = _observe(tmp_path)

    assert observed["commit"] == COMMIT_A


@pytest.mark.parametrize(
    "local_ref",
    [
        "refs/bisect/good",
        "refs/rewritten/topic",
        "refs/worktree/local-tip",
    ],
)
def test_linked_worktree_private_ref_namespaces_use_private_git_dir(
    tmp_path: Path,
    local_ref: str,
) -> None:
    common_dir, git_dir = _linked_repository(tmp_path)
    _write(common_dir / "refs/heads/feature", f"ref: {local_ref}\n")
    _write(git_dir / local_ref, f"{COMMIT_A}\n")
    _write(common_dir / local_ref, f"{COMMIT_B}\n")

    observed = _observe(tmp_path)

    assert observed["commit"] == COMMIT_A


def test_linked_worktree_private_ref_does_not_fall_back_to_common_packed_refs(
    tmp_path: Path,
) -> None:
    common_dir, _ = _linked_repository(tmp_path)
    local_ref = "refs/worktree/local-tip"
    _write(common_dir / "refs/heads/feature", f"ref: {local_ref}\n")
    _write(common_dir / "packed-refs", f"{COMMIT_B} {local_ref}\n")

    with pytest.raises(
        ValueError,
        match="unresolved worktree-local Git reference",
    ):
        _observe(tmp_path)


def test_linked_worktree_rejects_missing_backlink(tmp_path: Path) -> None:
    _, git_dir = _linked_repository(tmp_path)
    (git_dir / "gitdir").unlink()

    with pytest.raises(ValueError, match="backlink unavailable"):
        _observe(tmp_path)


def test_linked_worktree_rejects_mismatched_backlink(tmp_path: Path) -> None:
    _, git_dir = _linked_repository(tmp_path)
    other_marker = tmp_path / "other" / ".git"
    _write(other_marker, f"gitdir: {git_dir}\n")
    _write(git_dir / "gitdir", f"{other_marker}\n")

    with pytest.raises(ValueError, match="backlink mismatch"):
        _observe(tmp_path)
