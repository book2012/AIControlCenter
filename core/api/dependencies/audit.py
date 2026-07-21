"""Dependencies for the read-only governance audit API."""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from typing import Final

from core.governance.audit_query import AuditQueryService
from core.governance.audit_repository import SQLiteAuditRepository


APPLICATION_DIRECTORY_NAME: Final[str] = "AIControlCenter"
DATABASE_FILENAME: Final[str] = "model-governance-audit.sqlite3"

DATA_ROOT_ENV: Final[str] = "AICONTROLCENTER_DATA_ROOT"
SOURCE_COMMIT_ENV: Final[str] = "AICONTROLCENTER_SOURCE_COMMIT"
RUNTIME_RELEASE_ENV: Final[str] = "AICONTROLCENTER_RUNTIME_RELEASE"

_DEFAULT_SOURCE_COMMIT: Final[str] = "0" * 40
_DEFAULT_RUNTIME_RELEASE: Final[str] = "0" * 12

_GIT_SHA_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{40}$"
)
_RELEASE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{12}$"
)

_provider_lock = threading.RLock()
_query_service: AuditQueryService | None = None
_repository: SQLiteAuditRepository | None = None


class AuditDependencyError(RuntimeError):
    """Raised when audit dependency configuration fails closed."""


def application_support_root() -> Path:
    """Return the canonical AIControlCenter application root."""

    return (
        Path.home()
        / "Library"
        / "Application Support"
        / APPLICATION_DIRECTORY_NAME
    )


def runtime_root() -> Path:
    """Return the canonical immutable runtime root."""

    return application_support_root() / "runtime"


def resolve_data_root() -> Path:
    """Resolve application state without creating directories."""

    configured = os.environ.get(DATA_ROOT_ENV)

    if configured:
        candidate = Path(configured).expanduser()
    else:
        candidate = application_support_root() / "data"

    candidate = candidate.resolve(strict=False)
    immutable_root = runtime_root().resolve(strict=False)

    if (
        candidate == immutable_root
        or immutable_root in candidate.parents
    ):
        raise AuditDependencyError(
            "audit data root cannot be inside immutable runtime"
        )

    current_release = immutable_root / "current"

    try:
        resolved_release = current_release.resolve(strict=True)
    except FileNotFoundError:
        resolved_release = None

    if resolved_release is not None and (
        candidate == resolved_release
        or resolved_release in candidate.parents
    ):
        raise AuditDependencyError(
            "audit data root cannot be inside runtime release"
        )

    return candidate


def resolve_audit_database_path() -> Path:
    """Return the canonical audit database path."""

    return resolve_data_root() / DATABASE_FILENAME


def _source_commit() -> str:
    value = os.environ.get(
        SOURCE_COMMIT_ENV,
        _DEFAULT_SOURCE_COMMIT,
    )

    if _GIT_SHA_PATTERN.fullmatch(value) is None:
        raise AuditDependencyError(
            f"{SOURCE_COMMIT_ENV} must be a lowercase 40-character Git SHA"
        )

    return value


def _runtime_release() -> str:
    value = os.environ.get(
        RUNTIME_RELEASE_ENV,
        _DEFAULT_RUNTIME_RELEASE,
    )

    if _RELEASE_PATTERN.fullmatch(value) is None:
        raise AuditDependencyError(
            f"{RUNTIME_RELEASE_ENV} must be a lowercase 12-character release ID"
        )

    return value


def runtime_identity() -> tuple[str, str]:
    """Return validated source and runtime identities."""

    return (
        _source_commit(),
        _runtime_release(),
    )


def _utc_timestamp() -> str:
    """Create an RFC3339 UTC timestamp without naive datetime use."""

    from datetime import datetime, timezone

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def get_audit_repository() -> SQLiteAuditRepository:
    """Return the lazily initialized append-only repository."""

    global _repository

    if _repository is not None:
        return _repository

    with _provider_lock:
        if _repository is not None:
            return _repository

        source_commit, _ = runtime_identity()
        database_path = resolve_audit_database_path()

        repository = SQLiteAuditRepository(
            database_path,
            application_commit=source_commit,
            migrated_at=_utc_timestamp(),
        )

        repository.initialize()
        _repository = repository

        return repository


def get_audit_query_service() -> AuditQueryService:
    """Return the cached read-only audit query service."""

    global _query_service

    if _query_service is not None:
        return _query_service

    with _provider_lock:
        if _query_service is not None:
            return _query_service

        service = AuditQueryService(
            get_audit_repository()
        )

        _query_service = service

        return service


def reset_audit_dependencies() -> None:
    """Reset process-local providers for isolated tests."""

    global _query_service
    global _repository

    with _provider_lock:
        _query_service = None
        _repository = None
