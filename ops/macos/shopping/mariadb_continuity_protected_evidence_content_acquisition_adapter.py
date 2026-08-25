"""Fail-closed boundary and pure policy for protected-evidence acquisition."""

import stat

from core.secrets.mariadb_continuity_protected_evidence_acquisition_authorization import (
    ProtectedEvidenceAcquisitionInvocationCapability,
    ProtectedEvidenceAcquisitionRequest,
)
from core.secrets.mariadb_continuity_protected_evidence_content_acquisition import (
    ProtectedEvidenceContentAcquisitionError,
    ProtectedEvidenceContentAcquisitionErrorCode as Code,
    ProtectedEvidenceContentAcquisitionResult,
)
from core.secrets.mariadb_continuity_trusted_ownership_expectation import (
    TrustedOwnershipExpectation,
)

MAX_PROTECTED_EVIDENCE_CONTENT_BYTES = 1_048_576
MAXIMUM_SUCCESS_CONTENT_BYTES = MAX_PROTECTED_EVIDENCE_CONTENT_BYTES
MAXIMUM_BOUNDED_READ_BYTES = 1_048_577
PRODUCTION_ACQUISITION_AVAILABLE = False


def _leaf_mode_accepted(mode: int) -> bool:
    return stat.S_IMODE(mode) & ~0o600 == 0


def _fail(code: Code, cause: BaseException | None = None):
    error = ProtectedEvidenceContentAcquisitionError(code)
    if cause is None:
        raise error
    raise error from cause


class MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter:
    """Production boundary; unavailable until a separately frozen trusted composition exists."""

    def acquire(self, request: ProtectedEvidenceAcquisitionRequest,
                capability: ProtectedEvidenceAcquisitionInvocationCapability,
                trusted_identity: TrustedOwnershipExpectation,
                ) -> ProtectedEvidenceContentAcquisitionResult:
        # Deliberately fail before capability consumption and filesystem I/O.
        # There is no trusted Production path/ownership/human-auth composition yet.
        _fail(Code.INVALID_REQUEST)


class MacProtectedEvidenceContentAcquisitionMechanism:
    """Reserved mechanism; operational filesystem composition is not available."""

    def acquire(self, request: ProtectedEvidenceAcquisitionRequest,
                capability: ProtectedEvidenceAcquisitionInvocationCapability,
                trusted_identity: TrustedOwnershipExpectation,
                ) -> ProtectedEvidenceContentAcquisitionResult:
        # Parent-FD / leaf-open / content-read composition is intentionally FUTURE.
        # No Python value supplied by a caller is filesystem access authority.
        _fail(Code.INVALID_REQUEST)


__all__ = (
    "MAXIMUM_BOUNDED_READ_BYTES", "MAXIMUM_SUCCESS_CONTENT_BYTES",
    "MAX_PROTECTED_EVIDENCE_CONTENT_BYTES",
    "PRODUCTION_ACQUISITION_AVAILABLE",
    "MacProtectedEvidenceContentAcquisitionMechanism",
    "MariaDBContinuityProtectedEvidenceContentAcquisitionAdapter",
)
