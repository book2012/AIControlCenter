"""Read-only macOS inventory adapters."""

from .repository import (
    CaddyFileAdapter,
    ColimaContractAdapter,
    ComposeFileAdapter,
    GitRepositoryAdapter,
    LaunchdDesiredStateAdapter,
    RepositoryFileReader,
    RuntimeMetadataFileAdapter,
)
from .ingress import (
    CaddyIngressAdapter,
    ColimaIngressAdapter,
    ComposeIngressAdapter,
    IngressContractFileAdapter,
)

__all__ = (
    "CaddyFileAdapter",
    "ColimaContractAdapter",
    "ComposeFileAdapter",
    "GitRepositoryAdapter",
    "LaunchdDesiredStateAdapter",
    "RepositoryFileReader",
    "RuntimeMetadataFileAdapter",
    "CaddyIngressAdapter",
    "ColimaIngressAdapter",
    "ComposeIngressAdapter",
    "IngressContractFileAdapter",
)
