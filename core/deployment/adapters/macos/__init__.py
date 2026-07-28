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

__all__ = (
    "CaddyFileAdapter",
    "ColimaContractAdapter",
    "ComposeFileAdapter",
    "GitRepositoryAdapter",
    "LaunchdDesiredStateAdapter",
    "RepositoryFileReader",
    "RuntimeMetadataFileAdapter",
)
