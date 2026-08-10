from dataclasses import FrozenInstanceError, replace

import pytest

from core.governance.control_plane.application.evidence_policy import (
    EvidencePolicyReason,
    EvidencePolicyStatus,
    EvidenceStorageClass,
    EvidenceStorageDescriptor,
    evaluate_durable_evidence_storage,
)


def durable_descriptor() -> EvidenceStorageDescriptor:
    return EvidenceStorageDescriptor(
        storage_identity="operator-configured-governance-data",
        storage_class=EvidenceStorageClass.EXTERNAL_CONTROL_PLANE_DURABLE_DATA,
        ephemeral=False,
        private_tmp=False,
        repository_local=False,
        immutable_source_local=False,
        atomic_write_supported=True,
        restrictive_permissions_supported=True,
        durable_sync_supported=True,
        manifest_binding_supported=True,
        caller_supplied_reference_identities=True,
        value_free_enforced=True,
    )


def test_external_durable_control_plane_storage_is_accepted() -> None:
    result = evaluate_durable_evidence_storage(durable_descriptor())
    assert result.status is EvidencePolicyStatus.ACCEPT
    assert result.reason_codes == (EvidencePolicyReason.DURABLE_EVIDENCE_POLICY_SATISFIED,)


@pytest.mark.parametrize(
    ("change", "reason"),
    (
        ({"ephemeral": True}, EvidencePolicyReason.EPHEMERAL_STORAGE_FORBIDDEN),
        ({"private_tmp": True}, EvidencePolicyReason.PRIVATE_TMP_FORBIDDEN),
        ({"repository_local": True}, EvidencePolicyReason.REPOSITORY_STORAGE_FORBIDDEN),
        ({"immutable_source_local": True}, EvidencePolicyReason.IMMUTABLE_SOURCE_STORAGE_FORBIDDEN),
        ({"atomic_write_supported": False}, EvidencePolicyReason.ATOMIC_WRITE_REQUIRED),
        ({"restrictive_permissions_supported": False}, EvidencePolicyReason.RESTRICTIVE_PERMISSIONS_REQUIRED),
        ({"durable_sync_supported": False}, EvidencePolicyReason.DURABLE_SYNC_REQUIRED),
        ({"manifest_binding_supported": False}, EvidencePolicyReason.MANIFEST_BINDING_REQUIRED),
        (
            {"caller_supplied_reference_identities": False},
            EvidencePolicyReason.CALLER_SUPPLIED_REFERENCE_IDENTITIES_REQUIRED,
        ),
        ({"value_free_enforced": False}, EvidencePolicyReason.VALUE_FREE_EVIDENCE_REQUIRED),
    ),
)
def test_unsafe_storage_fact_is_rejected(change: dict[str, bool], reason: EvidencePolicyReason) -> None:
    result = evaluate_durable_evidence_storage(replace(durable_descriptor(), **change))
    assert result.status is EvidencePolicyStatus.REJECT
    assert reason in result.reason_codes


def test_non_external_storage_class_is_rejected() -> None:
    descriptor = replace(
        durable_descriptor(), storage_class=EvidenceStorageClass.TRANSIENT_CONTROLLER_REPORTS
    )
    assert evaluate_durable_evidence_storage(descriptor).reason_codes == (
        EvidencePolicyReason.EXTERNAL_CONTROL_PLANE_STORAGE_REQUIRED,
    )


def test_policy_is_deterministic_and_does_not_mutate_input() -> None:
    descriptor = durable_descriptor()
    before = descriptor
    assert evaluate_durable_evidence_storage(descriptor) == evaluate_durable_evidence_storage(descriptor)
    assert descriptor == before


def test_descriptor_and_result_are_immutable() -> None:
    descriptor = durable_descriptor()
    result = evaluate_durable_evidence_storage(descriptor)
    with pytest.raises(FrozenInstanceError):
        descriptor.ephemeral = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = EvidencePolicyStatus.REJECT  # type: ignore[misc]


def test_policy_has_no_filesystem_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("filesystem access is forbidden")

    monkeypatch.setattr("builtins.open", forbidden)
    assert evaluate_durable_evidence_storage(durable_descriptor()).status is EvidencePolicyStatus.ACCEPT
