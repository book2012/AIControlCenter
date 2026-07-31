from pathlib import Path

import pytest

from core.api.dependencies.audit import (
    DATA_ROOT_ENV,
    RUNTIME_RELEASE_ENV,
    SOURCE_COMMIT_ENV,
    AuditDependencyError,
    get_audit_query_service,
    get_audit_repository,
    reset_audit_dependencies,
    resolve_audit_database_path,
    resolve_data_root,
    runtime_identity,
)
from core.governance.audit_query import AuditQueryService
from core.governance.audit_repository import SQLiteAuditRepository


SOURCE_COMMIT = "94a12626a8995b8554af2af6311f41e019419116"
RUNTIME_RELEASE = "39fe04e3330e"


@pytest.fixture(autouse=True)
def reset_dependencies() -> None:
    reset_audit_dependencies()
    yield
    reset_audit_dependencies()


def configure_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        SOURCE_COMMIT_ENV,
        SOURCE_COMMIT,
    )
    monkeypatch.setenv(
        RUNTIME_RELEASE_ENV,
        RUNTIME_RELEASE,
    )


def test_default_database_path_is_application_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(DATA_ROOT_ENV, raising=False)
    path = resolve_audit_database_path()

    assert path.name == "model-governance-audit.sqlite3"
    assert path.parent.name == "data"
    assert path.parent.parent.name == "AIControlCenter"
    assert "runtime" not in path.parts


def test_data_root_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    override = tmp_path / "state"

    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(override),
    )

    assert resolve_data_root() == override.resolve()
    assert (
        resolve_audit_database_path()
        == override.resolve()
        / "model-governance-audit.sqlite3"
    )


def test_runtime_path_override_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = (
        Path.home()
        / "Library"
        / "Application Support"
        / "AIControlCenter"
        / "runtime"
        / "unsafe-data"
    )

    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(runtime),
    )

    with pytest.raises(
        AuditDependencyError,
        match="immutable runtime",
    ):
        resolve_data_root()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (SOURCE_COMMIT_ENV, "A" * 40),
        (SOURCE_COMMIT_ENV, "a" * 39),
        (RUNTIME_RELEASE_ENV, "B" * 12),
        (RUNTIME_RELEASE_ENV, "b" * 11),
    ],
)
def test_invalid_runtime_identity_is_denied(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    configure_identity(monkeypatch)
    monkeypatch.setenv(name, value)

    with pytest.raises(AuditDependencyError):
        runtime_identity()


def test_runtime_identity_is_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_identity(monkeypatch)

    assert runtime_identity() == (
        SOURCE_COMMIT,
        RUNTIME_RELEASE,
    )


def test_path_resolution_has_no_write_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "not-created"

    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(root),
    )

    path = resolve_audit_database_path()

    assert path.parent == root.resolve()
    assert root.exists() is False
    assert path.exists() is False


def test_repository_is_initialized_lazily(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "audit-state"

    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(root),
    )
    configure_identity(monkeypatch)

    database = resolve_audit_database_path()

    assert database.exists() is False

    repository = get_audit_repository()

    assert isinstance(
        repository,
        SQLiteAuditRepository,
    )
    assert database.exists() is True
    assert get_audit_repository() is repository


def test_nested_provider_initialization_does_not_deadlock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(tmp_path / "audit-state"),
    )
    configure_identity(monkeypatch)

    service = get_audit_query_service()

    assert isinstance(service, AuditQueryService)
    assert service.get_latest().to_dict()["empty"] is True



def test_query_service_is_cached(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(tmp_path / "audit-state"),
    )
    configure_identity(monkeypatch)

    first = get_audit_query_service()
    second = get_audit_query_service()

    assert isinstance(first, AuditQueryService)
    assert first is second


def test_reset_rebuilds_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        DATA_ROOT_ENV,
        str(tmp_path / "audit-state"),
    )
    configure_identity(monkeypatch)

    first = get_audit_query_service()

    reset_audit_dependencies()

    second = get_audit_query_service()

    assert first is not second
