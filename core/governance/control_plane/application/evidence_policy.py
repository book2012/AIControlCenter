"""Pure SEC-02A9 durable-evidence storage policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvidenceStorageClass(StrEnum):
    """Operator-observed storage classification, never a path inference."""

    EXTERNAL_CONTROL_PLANE_DURABLE_DATA = "EXTERNAL_CONTROL_PLANE_DURABLE_DATA"
    TRANSIENT_CONTROLLER_REPORTS = "TRANSIENT_CONTROLLER_REPORTS"
    REPOSITORY_DOCUMENTATION = "REPOSITORY_DOCUMENTATION"
    IMMUTABLE_APPLICATION_SOURCE = "IMMUTABLE_APPLICATION_SOURCE"
    OTHER = "OTHER"


class EvidencePolicyStatus(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class EvidencePolicyReason(StrEnum):
    DURABLE_EVIDENCE_POLICY_SATISFIED = "DURABLE_EVIDENCE_POLICY_SATISFIED"
    EXTERNAL_CONTROL_PLANE_STORAGE_REQUIRED = "EXTERNAL_CONTROL_PLANE_STORAGE_REQUIRED"
    EPHEMERAL_STORAGE_FORBIDDEN = "EPHEMERAL_STORAGE_FORBIDDEN"
    PRIVATE_TMP_FORBIDDEN = "PRIVATE_TMP_FORBIDDEN"
    REPOSITORY_STORAGE_FORBIDDEN = "REPOSITORY_STORAGE_FORBIDDEN"
    IMMUTABLE_SOURCE_STORAGE_FORBIDDEN = "IMMUTABLE_SOURCE_STORAGE_FORBIDDEN"
    ATOMIC_WRITE_REQUIRED = "ATOMIC_WRITE_REQUIRED"
    RESTRICTIVE_PERMISSIONS_REQUIRED = "RESTRICTIVE_PERMISSIONS_REQUIRED"
    DURABLE_SYNC_REQUIRED = "DURABLE_SYNC_REQUIRED"
    MANIFEST_BINDING_REQUIRED = "MANIFEST_BINDING_REQUIRED"
    CALLER_SUPPLIED_REFERENCE_IDENTITIES_REQUIRED = (
        "CALLER_SUPPLIED_REFERENCE_IDENTITIES_REQUIRED"
    )
    VALUE_FREE_EVIDENCE_REQUIRED = "VALUE_FREE_EVIDENCE_REQUIRED"


def _canonical_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty canonical text")
    return value


@dataclass(frozen=True, slots=True)
class EvidenceStorageDescriptor:
    """Caller-supplied facts about a configured evidence storage target."""

    storage_identity: str
    storage_class: EvidenceStorageClass
    ephemeral: bool
    private_tmp: bool
    repository_local: bool
    immutable_source_local: bool
    atomic_write_supported: bool
    restrictive_permissions_supported: bool
    durable_sync_supported: bool
    manifest_binding_supported: bool
    caller_supplied_reference_identities: bool
    value_free_enforced: bool

    def __post_init__(self) -> None:
        _canonical_text(self.storage_identity, "storage_identity")
        if not isinstance(self.storage_class, EvidenceStorageClass):
            raise TypeError("storage_class must be EvidenceStorageClass")
        for name in (
            "ephemeral", "private_tmp", "repository_local", "immutable_source_local",
            "atomic_write_supported", "restrictive_permissions_supported",
            "durable_sync_supported", "manifest_binding_supported",
            "caller_supplied_reference_identities", "value_free_enforced",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be boolean")


@dataclass(frozen=True, slots=True)
class EvidencePolicyEvaluation:
    status: EvidencePolicyStatus
    reason_codes: tuple[EvidencePolicyReason, ...]


def evaluate_durable_evidence_storage(
    descriptor: EvidenceStorageDescriptor,
) -> EvidencePolicyEvaluation:
    """Evaluate declared storage facts without inspection, I/O, or mutation."""
    if not isinstance(descriptor, EvidenceStorageDescriptor):
        raise TypeError("descriptor must be EvidenceStorageDescriptor")
    checks = (
        (descriptor.storage_class is not EvidenceStorageClass.EXTERNAL_CONTROL_PLANE_DURABLE_DATA,
         EvidencePolicyReason.EXTERNAL_CONTROL_PLANE_STORAGE_REQUIRED),
        (descriptor.ephemeral, EvidencePolicyReason.EPHEMERAL_STORAGE_FORBIDDEN),
        (descriptor.private_tmp, EvidencePolicyReason.PRIVATE_TMP_FORBIDDEN),
        (descriptor.repository_local, EvidencePolicyReason.REPOSITORY_STORAGE_FORBIDDEN),
        (descriptor.immutable_source_local,
         EvidencePolicyReason.IMMUTABLE_SOURCE_STORAGE_FORBIDDEN),
        (not descriptor.atomic_write_supported, EvidencePolicyReason.ATOMIC_WRITE_REQUIRED),
        (not descriptor.restrictive_permissions_supported,
         EvidencePolicyReason.RESTRICTIVE_PERMISSIONS_REQUIRED),
        (not descriptor.durable_sync_supported, EvidencePolicyReason.DURABLE_SYNC_REQUIRED),
        (not descriptor.manifest_binding_supported,
         EvidencePolicyReason.MANIFEST_BINDING_REQUIRED),
        (not descriptor.caller_supplied_reference_identities,
         EvidencePolicyReason.CALLER_SUPPLIED_REFERENCE_IDENTITIES_REQUIRED),
        (not descriptor.value_free_enforced,
         EvidencePolicyReason.VALUE_FREE_EVIDENCE_REQUIRED),
    )
    reasons = tuple(reason for rejected, reason in checks if rejected)
    if reasons:
        return EvidencePolicyEvaluation(EvidencePolicyStatus.REJECT, reasons)
    return EvidencePolicyEvaluation(
        EvidencePolicyStatus.ACCEPT,
        (EvidencePolicyReason.DURABLE_EVIDENCE_POLICY_SATISFIED,),
    )


__all__ = (
    "EvidencePolicyEvaluation", "EvidencePolicyReason", "EvidencePolicyStatus",
    "EvidenceStorageClass", "EvidenceStorageDescriptor", "evaluate_durable_evidence_storage",
)
