"""Default read-only dependency graph for the DPL API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.deployment.adapters.macos import (
    CaddyFileAdapter,
    CaddyIngressAdapter,
    ColimaContractAdapter,
    ColimaIngressAdapter,
    ComposeFileAdapter,
    ComposeIngressAdapter,
    GitRepositoryAdapter,
    IngressContractFileAdapter,
    LaunchdDesiredStateAdapter,
    RepositoryFileReader,
)
from core.deployment.application import (
    DeploymentApiComposer,
    IngressReadinessService,
    MacInventoryService,
)


class SystemUtcClock:
    def now_utc(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class NullAuditEvidenceSink:
    """Deliberately non-persistent M1 default."""

    def record(self, evidence: dict[str, Any]) -> None:
        return None


class UnavailableRuntimeMetadata:
    def observe_runtime_metadata(self) -> dict[str, Any]:
        raise RuntimeError("runtime observation not configured")


class UnavailableLaunchdSnapshots:
    def snapshot(self, label: str) -> None:
        return None


def _repository_files() -> RepositoryFileReader:
    return RepositoryFileReader(Path(__file__).resolve().parents[3])


def get_deployment_api_composer() -> DeploymentApiComposer:
    return DeploymentApiComposer(clock=SystemUtcClock(), sink=NullAuditEvidenceSink())


def get_mac_inventory_service() -> MacInventoryService:
    files = _repository_files()
    return MacInventoryService(
        git=GitRepositoryAdapter(files),
        runtime=UnavailableRuntimeMetadata(),
        launchd=LaunchdDesiredStateAdapter(
            files,
            (
                "deploy/macos/com.aihome.aicontrolcenter.plist",
                "ops/macos/caddy/com.aicontrolcenter.caddy.daemon.plist",
            ),
            UnavailableLaunchdSnapshots(),
        ),
        caddy=CaddyFileAdapter(files, "ops/macos/caddy/Caddyfile"),
        colima=ColimaContractAdapter(files, "ops/macos/colima/commerce-runtime.json"),
        compose=ComposeFileAdapter(files, "deploy/shopping/compose.yaml"),
        clock=SystemUtcClock(),
    )


def get_ingress_readiness_service() -> IngressReadinessService:
    files = _repository_files()
    return IngressReadinessService(
        contract=IngressContractFileAdapter(files, "config/deployment/ingress.json"),
        caddy=CaddyIngressAdapter(files, "ops/macos/caddy/Caddyfile"),
        colima=ColimaIngressAdapter(files, "ops/macos/colima/commerce-runtime.json"),
        compose=ComposeIngressAdapter(files, "deploy/shopping/compose.yaml"),
    )


__all__ = (
    "NullAuditEvidenceSink",
    "SystemUtcClock",
    "get_deployment_api_composer",
    "get_ingress_readiness_service",
    "get_mac_inventory_service",
)
