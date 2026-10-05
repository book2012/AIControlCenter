"""Focused contracts for STOREFRONT-PROD-RELEASE-MATERIALIZATION-01."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

import pytest

from core.shopping.storefront_prod_release_materialization import (
    ACCEPTED_GIT_COMMIT,
    ARCHIVE_SUBTREE,
    EXPECTED_FILE_COUNT,
    AuthorizationConsumedError,
    AuthorizationRequiredError,
    ReleaseMaterializationError,
    issue_authorization,
    materialize_release,
)
from core.shopping.storefront_prod_runtime import status_contract, validate_contract


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / ARCHIVE_SUBTREE
OPERATOR = ROOT / "core/shopping/storefront_prod_release_materialization.py"

@pytest.fixture(autouse=True)
def _clean_control_plane_status(monkeypatch):
    """Unit materialization tests run against an intentionally dirty dev worktree."""
    from core.shopping import storefront_prod_release_materialization as module

    original_git = module._git

    def clean_git(repo: Path, *args: str) -> str:
        if args == ("status", "--porcelain=v1", "--untracked-files=all"):
            return ""
        return original_git(repo, *args)

    monkeypatch.setattr(module, "_git", clean_git)



def _archive_files() -> dict[str, bytes]:
    raw = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", ACCEPTED_GIT_COMMIT, "--", ARCHIVE_SUBTREE],
        check=True,
        capture_output=True,
    ).stdout
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        prefix = ARCHIVE_SUBTREE + "/"
        for member in archive:
            if member.isfile() and member.name.startswith(prefix):
                result[member.name[len(prefix):]] = archive.extractfile(member).read()
    return result


def _materialize(tmp_path: Path):
    root = tmp_path / "storefront-prod"
    authorization = issue_authorization(root)
    manifest = materialize_release(ROOT, root, authorization=authorization)
    return root, authorization, manifest


def test_exact_accepted_payload_is_selected_without_reading_head_or_worktree(tmp_path, monkeypatch):
    from core.shopping import storefront_prod_release_materialization as module

    original_git = module._git

    def reject_head_inspection(repo: Path, *args: str) -> str:
        if args == ("rev-parse", "HEAD"):
            raise AssertionError("materializer inspected control-plane HEAD")
        return original_git(repo, *args)

    monkeypatch.setattr(module, "_git", reject_head_inspection)

    original = PLUGIN / "ai-shopping-storefront.php"
    original_read_bytes = Path.read_bytes

    def reject_worktree_reads(path: Path):
        if path.absolute() == original.absolute():
            raise AssertionError("materializer read the working-tree plugin")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", reject_worktree_reads)

    root, _, manifest = _materialize(tmp_path)

    assert manifest["git_commit"] == ACCEPTED_GIT_COMMIT
    assert manifest["source_provenance"]["method"] == "git_archive"
    assert (
        root
        / "releases"
        / ACCEPTED_GIT_COMMIT
        / "ai-shopping-storefront"
        / "ai-shopping-storefront.php"
    ).read_bytes()


def test_dirty_control_plane_fails_before_authorization_is_consumed(tmp_path, monkeypatch):
    from core.shopping import storefront_prod_release_materialization as module

    clean_git = module._git

    def dirty_git(repo: Path, *args: str) -> str:
        if args == ("status", "--porcelain=v1", "--untracked-files=all"):
            return " M tracked-change"
        return clean_git(repo, *args)

    monkeypatch.setattr(module, "_git", dirty_git)

    root = tmp_path / "storefront-prod"
    authorization = issue_authorization(root)

    with pytest.raises(
        ReleaseMaterializationError,
        match="control-plane worktree must be clean",
    ):
        materialize_release(
            ROOT,
            root,
            authorization=authorization,
        )

    assert not root.exists()

    # The failed cleanliness preflight must not consume one-shot authority.
    monkeypatch.setattr(module, "_git", clean_git)

    manifest = materialize_release(
        ROOT,
        root,
        authorization=authorization,
    )

    assert manifest["git_commit"] == ACCEPTED_GIT_COMMIT
    assert manifest["source_clean"] is True
    assert manifest["source_provenance"]["working_tree_clean"] is True


def test_payload_identity_is_the_accepted_archive_and_has_299_files(tmp_path):
    root, _, manifest = _materialize(tmp_path)
    files = _archive_files()
    payload = root / "releases" / ACCEPTED_GIT_COMMIT / "ai-shopping-storefront"
    assert len(files) == EXPECTED_FILE_COUNT == 299
    assert manifest["file_count"] == 299
    assert manifest["relative_file_paths"] == sorted(files)
    for relative, content in files.items():
        assert (payload / relative).read_bytes() == content
        item = next(entry for entry in manifest["files"] if entry["path"] == relative)
        assert item["sha256"] == hashlib.sha256(content).hexdigest()


def test_manifest_is_deterministic_for_the_same_accepted_archive(tmp_path):
    first_root, _, first = _materialize(tmp_path / "first")
    second_root, _, second = _materialize(tmp_path / "second")
    first = dict(first)
    second = dict(second)
    first.pop("release_path")
    second.pop("release_path")
    assert first == second
    assert first_root != second_root


def _malicious_archive(*members: tuple[str, str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, kind, content in members:
            info = tarfile.TarInfo(name)
            if kind == "directory":
                info.type = tarfile.DIRTYPE
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = "outside"
            else:
                info.size = len(content)
            archive.addfile(info, io.BytesIO(content) if kind == "file" else None)
    return buffer.getvalue()


def test_symlink_rejection(tmp_path, monkeypatch):
    from core.shopping import storefront_prod_release_materialization as module

    monkeypatch.setattr(module, "_git_archive", lambda repo, commit: _malicious_archive(
        (ARCHIVE_SUBTREE, "directory", b""),
        (ARCHIVE_SUBTREE + "/link", "symlink", b""),
    ))
    authorization = issue_authorization(tmp_path / "root")
    with pytest.raises(ReleaseMaterializationError, match="symlink"):
        materialize_release(ROOT, tmp_path / "root", authorization=authorization)
    assert not (tmp_path / "root").exists()


def test_path_traversal_rejection(tmp_path, monkeypatch):
    from core.shopping import storefront_prod_release_materialization as module

    monkeypatch.setattr(module, "_git_archive", lambda repo, commit: _malicious_archive(
        (ARCHIVE_SUBTREE, "directory", b""),
        (ARCHIVE_SUBTREE + "/../escape", "file", b"escape"),
    ))
    authorization = issue_authorization(tmp_path / "root")
    with pytest.raises(ReleaseMaterializationError, match="traversal"):
        materialize_release(ROOT, tmp_path / "root", authorization=authorization)
    assert not (tmp_path / "root").exists()


def test_conflicting_release_rejection(tmp_path):
    root = tmp_path / "root"
    target = root / "releases" / ACCEPTED_GIT_COMMIT / "ai-shopping-storefront"
    target.mkdir(parents=True)
    (target / "conflict.txt").write_text("user content")
    authorization = issue_authorization(root)
    with pytest.raises(ReleaseMaterializationError, match="already exists"):
        materialize_release(ROOT, root, authorization=authorization)
    assert (target / "conflict.txt").read_text() == "user content"



def _write_prior_release(root: Path) -> tuple[Path, str]:
    commit = "1" * 40
    release = root / "releases" / commit / "ai-shopping-storefront"
    release.mkdir(parents=True)
    (release / "ai-shopping-storefront.php").write_text("<?php // prior release\n")
    manifest = {
        "schema_version": 1,
        "environment": "prod",
        "service": "storefront",
        "git_commit": commit,
        "plugin_version": "0.19.0",
        "presentation_identifier": "SHOP_MEDIA_003_AGACHICHI",
        "release_path": str(release),
        "created_at": "2026-10-04T00:00:00Z",
        "source_clean": True,
        "source_provenance": {
            "method": "git_archive",
            "archived_revision": commit,
            "working_tree_clean": True,
        },
    }
    raw = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    (root / "current.json").write_text(raw)
    (release / ".aicontrolcenter-release.json").write_text(raw)
    return release, raw


def test_existing_prior_release_is_preserved_during_promotion(tmp_path):
    root = tmp_path / "root"
    prior_release, _ = _write_prior_release(root)
    authorization = issue_authorization(root)

    manifest = materialize_release(ROOT, root, authorization=authorization)

    current = json.loads((root / "current.json").read_text())
    assert current["git_commit"] == ACCEPTED_GIT_COMMIT
    assert manifest["git_commit"] == ACCEPTED_GIT_COMMIT
    assert prior_release.is_dir()
    assert (prior_release / "ai-shopping-storefront.php").is_file()
    assert validate_contract(root)["valid"] is True


def test_failed_promotion_restores_previous_current_and_removes_new_release(tmp_path, monkeypatch):
    from core.shopping import storefront_prod_release_materialization as module
    from core.shopping.storefront_prod_runtime import ReleaseManifestError

    root = tmp_path / "root"
    prior_release, prior_current = _write_prior_release(root)
    authorization = issue_authorization(root)

    def reject_new_release(_root: Path):
        raise ReleaseManifestError("simulated validation failure")

    monkeypatch.setattr(module, "validate_release", reject_new_release)

    with pytest.raises(ReleaseMaterializationError, match="failed runtime validation"):
        materialize_release(ROOT, root, authorization=authorization)

    assert (root / "current.json").read_text() == prior_current
    assert prior_release.is_dir()
    assert not (root / "releases" / ACCEPTED_GIT_COMMIT).exists()

def test_authorization_is_required_and_single_use(tmp_path):
    root = tmp_path / "root"
    with pytest.raises(AuthorizationRequiredError):
        materialize_release(ROOT, root)
    assert not root.exists()
    authorization = issue_authorization(root)
    materialize_release(ROOT, root, authorization=authorization)
    with pytest.raises(AuthorizationConsumedError):
        materialize_release(ROOT, tmp_path / "second", authorization=authorization)
    assert not (tmp_path / "second").exists()


def test_file_authorization_is_consumed_before_release_write(tmp_path):
    root = tmp_path / "root"
    authorization_file = tmp_path / "authorization.json"
    from core.shopping.storefront_prod_release_materialization import save_authorization

    authorization = issue_authorization(root)
    save_authorization(authorization_file, authorization)
    from core.shopping.storefront_prod_release_materialization import load_authorization

    loaded = load_authorization(authorization_file, root)
    materialize_release(ROOT, root, authorization=loaded, authorization_file=authorization_file)
    assert json.loads(authorization_file.read_text())["consumed"] is True


def test_existing_runtime_contract_accepts_materialized_release(tmp_path):
    root, _, manifest = _materialize(tmp_path)
    assert validate_contract(root)["valid"] is True
    status = status_contract(root)
    assert status["validation"]["valid"] is True
    assert status["release"]["git_commit"] == ACCEPTED_GIT_COMMIT
    assert status["release"]["path"] == manifest["release_path"]


def test_operator_has_no_runtime_lifecycle_or_external_system_code():
    source = OPERATOR.read_text()
    lowered = source.lower()
    assert not any(token in lowered for token in ("docker", "caddy", "database", "ubuntu", "compose", "woocommerce"))
    assert "git" in lowered and "archive" in lowered
