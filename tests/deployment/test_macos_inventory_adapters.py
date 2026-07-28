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
