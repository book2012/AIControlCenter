"""SQLite governance operations adapter API."""

from .backup import (
    BackupVerificationError,
    BackupVerificationResult,
    SQLiteOnlineBackupVerifier,
)
from .codec import (
    PayloadIntegrityError,
    event_from_row,
    event_payload_sha256,
    event_to_parameters,
)
from .repository import (
    IdempotencyConflictError,
    RepositoryConfigurationError,
    SQLiteOperationsEventRepository,
)
from .schema import (
    ADAPTER_SCHEMA_VERSION,
    REQUIRED_OBJECTS,
    SCHEMA_SQL,
    TABLE_NAME,
)

__all__ = [
    "ADAPTER_SCHEMA_VERSION",
    "BackupVerificationError",
    "BackupVerificationResult",
    "IdempotencyConflictError",
    "PayloadIntegrityError",
    "REQUIRED_OBJECTS",
    "RepositoryConfigurationError",
    "SCHEMA_SQL",
    "SQLiteOnlineBackupVerifier",
    "SQLiteOperationsEventRepository",
    "TABLE_NAME",
    "event_from_row",
    "event_payload_sha256",
    "event_to_parameters",
]
