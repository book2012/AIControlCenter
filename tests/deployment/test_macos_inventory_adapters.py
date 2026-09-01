from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.deployment.adapters.macos import (
    CaddyFileAdapter,
    ColimaContractAdapter,
    ComposeFileAdapter,
    GitRepositoryAdapter,
    LaunchdDesiredStateAdapter,
    RepositoryFileReader,
    RuntimeMetadataFileAdapter,
)
from core.deployment.application import MacInventoryService

ROOT = Path(__file__).parents[2]


class Snapshots:
    def __init__(self, values: dict[str, str | None]) -> None:
        self.values = values

    def snapshot(self, label: str) -> str | None:
        return self.values.get(label)


class Clock:
    def now_utc(self) -> str:
        return "2026-07-28T00:00:00Z"


def test_git_identity_mapping(tmp_path: Path) -> None:
    git = tmp_path / ".git"
    (git / "refs/heads/feature").mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/feature/dpl\n", encoding="utf-8")
    (git / "refs/heads/feature/dpl").write_text("a" * 40 + "\n", encoding="utf-8")
    result = GitRepositoryAdapter(RepositoryFileReader(tmp_path)).observe_git_identity()
    assert result["repository_id"] == "AIControlCenter"
    assert result["branch"] == "feature/dpl"
    assert result["commit"] == "a" * 40


def _write_head(tmp_path: Path, value: str) -> GitRepositoryAdapter:
    git = tmp_path / ".git"
    git.mkdir(exist_ok=True)
    (git / "HEAD").write_text(value, encoding="utf-8")
    return GitRepositoryAdapter(RepositoryFileReader(tmp_path))


def test_git_identity_resolves_branch_only_in_packed_refs(tmp_path: Path) -> None:
    adapter = _write_head(tmp_path, "ref: refs/heads/feature/packed\n")
    (tmp_path / ".git/packed-refs").write_text(
        "# pack-refs with: peeled fully-peeled sorted\n"
        + "b" * 40 + " refs/heads/feature/packed\n"
        + "^" + "c" * 40 + "\n",
        encoding="utf-8",
    )
    result = adapter.observe_git_identity()
    assert result["branch"] == "feature/packed"
    assert result["commit"] == "b" * 40


def test_git_identity_resolves_loose_symbolic_branch_ref(tmp_path: Path) -> None:
    adapter = _write_head(tmp_path, "ref: refs/heads/current\n")
    git = tmp_path / ".git"
    (git / "refs/heads").mkdir(parents=True)
    (git / "refs/heads/current").write_text(
        "ref: refs/heads/target\n", encoding="utf-8"
    )
    (git / "refs/heads/target").write_text("c" * 40 + "\n", encoding="utf-8")
    result = adapter.observe_git_identity()
    assert result["branch"] == "current"
    assert result["commit"] == "c" * 40


def test_git_identity_accepts_detached_full_object_id(tmp_path: Path) -> None:
    result = _write_head(tmp_path, "d" * 40 + "\n").observe_git_identity()
    assert result["branch"] == "HEAD"
    assert result["commit"] == "d" * 40


def test_packed_refs_use_exact_name_not_similar_prefix(tmp_path: Path) -> None:
    adapter = _write_head(tmp_path, "ref: refs/heads/release\n")
    (tmp_path / ".git/packed-refs").write_text(
        "e" * 40 + " refs/heads/release-candidate\n"
        + "f" * 40 + " refs/heads/release\n",
        encoding="utf-8",
    )
    assert adapter.observe_git_identity()["commit"] == "f" * 40


@pytest.mark.parametrize(
    "setup",
    [
        "missing",
        "malformed-packed",
        "abbreviated",
        "invalid-object",
        "whitespace-object",
        "unsafe",
        "cycle",
        "depth",
    ],
)
def test_git_identity_fails_closed_for_invalid_refs(tmp_path: Path, setup: str) -> None:
    git = tmp_path / ".git"
    (git / "refs/heads").mkdir(parents=True)
    head = "ref: refs/heads/missing\n"
    if setup == "malformed-packed":
        (git / "packed-refs").write_text(
            "short refs/heads/missing\n", encoding="utf-8"
        )
    elif setup == "abbreviated":
        head = "a" * 12 + "\n"
    elif setup == "invalid-object":
        head = "g" * 40 + "\n"
    elif setup == "whitespace-object":
        head = "a" * 40 + " \n"
    elif setup == "unsafe":
        head = "ref: refs/heads/../secret\n"
    elif setup == "cycle":
        head = "ref: refs/heads/one\n"
        (git / "refs/heads/one").write_text("ref: refs/heads/two\n", encoding="utf-8")
        (git / "refs/heads/two").write_text("ref: refs/heads/one\n", encoding="utf-8")
    elif setup == "depth":
        head = "ref: refs/heads/0\n"
        for index in range(17):
            (git / f"refs/heads/{index}").write_text(
                f"ref: refs/heads/{index + 1}\n", encoding="utf-8"
            )
    adapter = _write_head(tmp_path, head)
    with pytest.raises(ValueError):
        adapter.observe_git_identity()


def test_duplicate_exact_packed_ref_is_rejected(tmp_path: Path) -> None:
    adapter = _write_head(tmp_path, "ref: refs/heads/duplicate\n")
    (tmp_path / ".git/packed-refs").write_text(
        "a" * 40 + " refs/heads/duplicate\n"
        + "b" * 40 + " refs/heads/duplicate\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="ambiguous"):
        adapter.observe_git_identity()


def _write_linked_worktree(
    tmp_path: Path,
    head: str,
) -> tuple[GitRepositoryAdapter, Path, Path]:
    common = tmp_path / "common.git"
    git_dir = common / "worktrees" / "fixture"
    worktree = tmp_path / "worktree"

    worktree.mkdir()
    git_dir.mkdir(parents=True)

    (worktree / ".git").write_text(
        f"gitdir: {git_dir}\n",
        encoding="utf-8",
    )
    (git_dir / "HEAD").write_text(head, encoding="utf-8")
    (git_dir / "commondir").write_text("../..\n", encoding="utf-8")
    (git_dir / "gitdir").write_text(
        str(worktree / ".git") + "\n",
        encoding="utf-8",
    )

    return (
        GitRepositoryAdapter(RepositoryFileReader(worktree)),
        common,
        git_dir,
    )


def test_git_identity_resolves_linked_worktree_shared_ref(
    tmp_path: Path,
) -> None:
    adapter, common, _ = _write_linked_worktree(
        tmp_path,
        "ref: refs/heads/feature/linked\n",
    )

    ref = common / "refs/heads/feature/linked"
    ref.parent.mkdir(parents=True)
    ref.write_text("1" * 40 + "\n", encoding="utf-8")

    result = adapter.observe_git_identity()

    assert result["branch"] == "feature/linked"
    assert result["commit"] == "1" * 40


def test_git_identity_resolves_linked_worktree_shared_packed_ref(
    tmp_path: Path,
) -> None:
    adapter, common, _ = _write_linked_worktree(
        tmp_path,
        "ref: refs/heads/feature/packed-linked\n",
    )

    (common / "packed-refs").write_text(
        "2" * 40 + " refs/heads/feature/packed-linked\n",
        encoding="utf-8",
    )

    result = adapter.observe_git_identity()

    assert result["branch"] == "feature/packed-linked"
    assert result["commit"] == "2" * 40


def test_git_identity_rejects_malformed_gitfile(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text(
        "not-a-gitdir\n",
        encoding="utf-8",
    )

    adapter = GitRepositoryAdapter(RepositoryFileReader(worktree))

    with pytest.raises(ValueError):
        adapter.observe_git_identity()


def test_git_identity_rejects_missing_gitdir_target(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text(
        f"gitdir: {tmp_path / 'missing.git'}\n",
        encoding="utf-8",
    )

    adapter = GitRepositoryAdapter(RepositoryFileReader(worktree))

    with pytest.raises(ValueError):
        adapter.observe_git_identity()


def test_git_identity_rejects_missing_commondir_target(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    git_dir = tmp_path / "metadata" / "worktrees" / "fixture"

    worktree.mkdir()
    git_dir.mkdir(parents=True)

    (worktree / ".git").write_text(
        f"gitdir: {git_dir}\n",
        encoding="utf-8",
    )
    (git_dir / "HEAD").write_text(
        "ref: refs/heads/feature/missing-common\n",
        encoding="utf-8",
    )
    (git_dir / "commondir").write_text(
        "../../missing-common\n",
        encoding="utf-8",
    )

    adapter = GitRepositoryAdapter(RepositoryFileReader(worktree))

    with pytest.raises(ValueError):
        adapter.observe_git_identity()


def test_runtime_metadata_mapping() -> None:
    result = RuntimeMetadataFileAdapter(
        RepositoryFileReader(ROOT),
        "tests/fixtures/deployment/runtime-metadata.json",
    ).observe_runtime_metadata()
    assert result["runtime_mode"] == "shadow"
    assert result["short_commit"] == "0880aba3c616"


def test_launchd_desired_and_current_state_parsing() -> None:
    path = "ops/macos/caddy/com.aicontrolcenter.caddy.daemon.plist"
    result = LaunchdDesiredStateAdapter(
        RepositoryFileReader(ROOT),
        (path,),
        Snapshots({"com.aicontrolcenter.caddy": "state = running\npid = 42"}),
    ).observe_launchd()
    assert result["services"][0]["current"] == "running"
    assert result["services"][0]["desired"] == "loaded"
    assert result["state"] == "present"


def test_launchd_unavailable_is_degraded() -> None:
    result = LaunchdDesiredStateAdapter(
        RepositoryFileReader(ROOT),
        ("ops/macos/caddy/com.aicontrolcenter.caddy.daemon.plist",),
        Snapshots({}),
    ).observe_launchd()
    assert result["state"] == "degraded"
    assert result["services"][0]["current"] == "unavailable"
    assert result["errors"][0]["code"] == "launchd-observation-unavailable"


def test_caddy_sole_edge_mapping() -> None:
    result = CaddyFileAdapter(
        RepositoryFileReader(ROOT), "ops/macos/caddy/Caddyfile"
    ).observe_caddy_desired_state()
    assert result["owner"] == "host-caddy"
    assert result["sole_public_edge"] is True
    assert result["upstreams"] == ["127.0.0.1:58081"]


def test_colima_contract_mapping() -> None:
    result = ColimaContractAdapter(
        RepositoryFileReader(ROOT), "ops/macos/colima/commerce-runtime.json"
    ).observe_colima_contract()
    assert result["profile"] == "aicontrolcenter-commerce"
    assert result["public_ingress_owner"] == "host-caddy"
    assert result["ubuntu_runtime_allowed"] is False


def test_compose_mapping_and_loopback_exposure() -> None:
    result = ComposeFileAdapter(
        RepositoryFileReader(ROOT), "deploy/shopping/compose.yaml"
    ).observe_compose_desired_state()
    assert result["wordpress"] is True
    assert result["woocommerce"] is True
    assert result["wordpress_exposure"] == "loopback-only"
    assert result["direct_public_ports"] is False
    assert result["internal_networks"] == ["shopping_internal"]


def test_repository_backed_adapters_compose_schema_valid_inventory() -> None:
    files = RepositoryFileReader(ROOT)
    inventory = MacInventoryService(
        git=GitRepositoryAdapter(files),
        runtime=RuntimeMetadataFileAdapter(
            files, "tests/fixtures/deployment/runtime-metadata.json"
        ),
        launchd=LaunchdDesiredStateAdapter(
            files,
            (
                "ops/macos/caddy/com.aicontrolcenter.caddy.daemon.plist",
                "ops/macos/launchd/com.aicontrolcenter.api.shadow.plist",
            ),
            Snapshots({
                "com.aicontrolcenter.caddy": "state = running",
                "com.aicontrolcenter.api.shadow": "state = running",
            }),
        ),
        caddy=CaddyFileAdapter(files, "ops/macos/caddy/Caddyfile"),
        colima=ColimaContractAdapter(
            files, "ops/macos/colima/commerce-runtime.json"
        ),
        compose=ComposeFileAdapter(files, "deploy/shopping/compose.yaml"),
        clock=Clock(),
    ).collect()
    assert inventory["read_only"] is True
    assert all(item["state"] == "present" for item in inventory["items"])


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "ok/../../secret"])
def test_repository_reader_rejects_path_traversal(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match="traversal"):
        RepositoryFileReader(tmp_path).read_text(path)


@pytest.mark.parametrize(
    ("adapter", "content"),
    [
        ("runtime", "[]"),
        ("colima", "{}"),
        ("compose", "services: []"),
    ],
)
def test_malformed_adapter_data_is_rejected(tmp_path: Path, adapter: str, content: str) -> None:
    (tmp_path / "input").write_text(content, encoding="utf-8")
    files = RepositoryFileReader(tmp_path)
    instance = {
        "runtime": RuntimeMetadataFileAdapter(files, "input").observe_runtime_metadata,
        "colima": ColimaContractAdapter(files, "input").observe_colima_contract,
        "compose": ComposeFileAdapter(files, "input").observe_compose_desired_state,
    }[adapter]
    with pytest.raises((ValueError, json.JSONDecodeError)):
        instance()
