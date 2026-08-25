"""Opaque protected content values and fail-closed acquisition outcomes."""

from dataclasses import dataclass, field
from enum import Enum


class ProtectedEvidenceContentAcquisitionErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORIZATION_NOT_COMMITTED = "AUTHORIZATION_NOT_COMMITTED"
    PARENT_UNSAFE = "PARENT_UNSAFE"
    LEAF_UNSAFE = "LEAF_UNSAFE"
    CONTENT_EMPTY = "CONTENT_EMPTY"
    CONTENT_SIZE_LIMIT_EXCEEDED = "CONTENT_SIZE_LIMIT_EXCEEDED"
    CONTENT_UNSTABLE = "CONTENT_UNSTABLE"
    READ_FAILED = "READ_FAILED"


class ProtectedEvidenceContentAcquisitionError(RuntimeError):
    def __init__(self, code: ProtectedEvidenceContentAcquisitionErrorCode):
        self.code = code
        super().__init__(code.value)


@dataclass(frozen=True, slots=True, init=False, repr=False)
class ProtectedEvidenceContent:
    """In-process opaque bytes; never JSON, logged, hashed, or serialized."""

    _content: bytes

    def __new__(cls):
        raise TypeError("content is constructed only by the acquisition boundary")

    def __repr__(self) -> str:
        return "ProtectedEvidenceContent(<opaque>)"

    def __copy__(self):
        raise TypeError("protected content cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("protected content cannot be deep-copied")

    def __reduce__(self):
        raise TypeError("protected content cannot be serialized")

    def __hash__(self):
        raise TypeError("protected content cannot be hashed")

    def _content_for_next_repository_boundary(self) -> bytes:
        return self._content


def _acquired_content(content: bytes) -> ProtectedEvidenceContent:
    if type(content) is not bytes:
        raise TypeError("content must be bytes")
    value = object.__new__(ProtectedEvidenceContent)
    object.__setattr__(value, "_content", content)
    return value


@dataclass(frozen=True, slots=True)
class ProtectedEvidenceContentAcquisitionResult:
    content: ProtectedEvidenceContent
    content_acquired_from_stable_binding: bool = field(default=True, init=False)
    evidence_admitted: bool = field(default=False, init=False)
    evidence_verified: bool = field(default=False, init=False)
    provenance_valid: bool = field(default=False, init=False)
    integrity_valid: bool = field(default=False, init=False)
    trusted_issuer: bool = field(default=False, init=False)
    recover_evidence_sufficient: bool = field(default=False, init=False)
    production_validation_ready: bool = field(default=False, init=False)
    production_authorization: bool = field(default=False, init=False)
    execution_authority: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self.content) is not ProtectedEvidenceContent:
            raise TypeError("content must be exactly ProtectedEvidenceContent")


__all__ = (
    "ProtectedEvidenceContent", "ProtectedEvidenceContentAcquisitionError",
    "ProtectedEvidenceContentAcquisitionErrorCode", "ProtectedEvidenceContentAcquisitionResult",
)
