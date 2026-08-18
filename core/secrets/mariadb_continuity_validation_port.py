"""Narrow read-only port for MariaDB continuity validation."""

from typing import Protocol, runtime_checkable

from core.secrets.mariadb_continuity_validation import (
    MariaDBContinuityValidationRequest,
    MariaDBContinuityValidationResult,
)


@runtime_checkable
class MariaDBContinuityValidationPort(Protocol):
    def validate_once(
        self, request: MariaDBContinuityValidationRequest, capability: object
    ) -> MariaDBContinuityValidationResult:
        """Observe one externally authorized capability invocation at most."""

        ...
