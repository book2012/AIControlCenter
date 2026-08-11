"""Read-only runtime composition for durable ProductDraft queries."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
from typing import Callable

from core.runtime.data_paths import DATA_ROOT_ENV

from .persistence import (
    DatabasePathPolicy,
    DurableDatabasePathPolicy,
    SQLiteProductDraftStore,
    resolve_product_draft_database_path,
)
from .persistence.schema import ShoppingDatabaseError, connect_database, validate_database
from .read import (
    ProductDraftQueryService,
    ProductDraftReadUnavailable,
    ProductDraftReadSource,
    UnavailableProductDraftReadSource,
)
from .models import ProductDraftRevision


@dataclass(frozen=True, slots=True)
class ProductDraftCapability:
    configured: bool
    database_available: bool
    schema_valid: bool
    durable_reads_available: bool
    reason_code: str


@dataclass(frozen=True, slots=True)
class ProductDraftReadRuntime:
    query_service: ProductDraftQueryService
    capability: ProductDraftCapability


class FailClosedProductDraftReadSource:
    """Translate only storage failures that can occur after startup validation."""

    def __init__(self, source: ProductDraftReadSource) -> None:
        self._source = source

    def is_available(self) -> bool:
        return self._source.is_available()

    @staticmethod
    def _unavailable(error: Exception) -> ProductDraftReadUnavailable:
        return ProductDraftReadUnavailable("ProductDraft read source unavailable")

    def list_revisions(self) -> tuple[ProductDraftRevision, ...]:
        try:
            return self._source.list_revisions()
        except (OSError, sqlite3.Error, ShoppingDatabaseError, ValueError, TypeError, KeyError) as error:
            raise self._unavailable(error) from error

    def fetch_current(self, draft_id: str) -> ProductDraftRevision | None:
        try:
            return self._source.fetch_current(draft_id)
        except (OSError, sqlite3.Error, ShoppingDatabaseError, ValueError, TypeError, KeyError) as error:
            raise self._unavailable(error) from error

    def fetch_revision(self, draft_id: str, revision_id: str) -> ProductDraftRevision | None:
        try:
            return self._source.fetch_revision(draft_id, revision_id)
        except (OSError, sqlite3.Error, ShoppingDatabaseError, ValueError, TypeError, KeyError) as error:
            raise self._unavailable(error) from error


def _unavailable_capability(*, configured: bool, database_available: bool = False,
                            schema_valid: bool = False, reason_code: str) -> ProductDraftCapability:
    return ProductDraftCapability(configured, database_available, schema_valid, False, reason_code)


def build_product_draft_read_runtime(
    *,
    path_resolver: Callable[[], Path] = resolve_product_draft_database_path,
    path_policy: DatabasePathPolicy | None = None,
) -> ProductDraftReadRuntime:
    """Validate an existing DB read-only and compose a fail-closed query service."""
    configured = bool(os.environ.get(DATA_ROOT_ENV, "").strip())
    try:
        database_path = path_resolver()
    except (OSError, ValueError):
        reason = "DATABASE_INVALID" if configured else "DATA_ROOT_UNCONFIGURED"
        capability = _unavailable_capability(configured=configured, reason_code=reason)
        return ProductDraftReadRuntime(
            ProductDraftQueryService(UnavailableProductDraftReadSource()), capability
        )

    if not database_path.is_file():
        capability = _unavailable_capability(configured=True, reason_code="DATABASE_MISSING")
        return ProductDraftReadRuntime(
            ProductDraftQueryService(UnavailableProductDraftReadSource()), capability
        )

    try:
        connection = connect_database(database_path, read_only=True)
        try:
            validate_database(connection)
        finally:
            connection.close()
        policy = path_policy or DurableDatabasePathPolicy()
        store = SQLiteProductDraftStore(database_path, path_policy=policy)
    except (OSError, sqlite3.Error, ShoppingDatabaseError, ValueError):
        capability = _unavailable_capability(
            configured=True, database_available=True, reason_code="DATABASE_INVALID"
        )
        return ProductDraftReadRuntime(
            ProductDraftQueryService(UnavailableProductDraftReadSource()), capability
        )

    capability = ProductDraftCapability(True, True, True, True, "AVAILABLE")
    source = FailClosedProductDraftReadSource(store)
    return ProductDraftReadRuntime(ProductDraftQueryService(source), capability)


__all__ = (
    "FailClosedProductDraftReadSource",
    "ProductDraftCapability",
    "ProductDraftReadRuntime",
    "build_product_draft_read_runtime",
)
