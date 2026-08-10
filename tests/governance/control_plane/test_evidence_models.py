import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timezone

import pytest

from core.governance.control_plane.domain import (
    DuplicateEvidenceReference, EvidenceArtifactReference, GovernanceEvidenceBundle,
    GovernanceEvidenceManifest, InvalidEvidenceBundle,
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def ref(kind: str, identity: str | None = None, lifecycle: str = "lifecycle-1") -> EvidenceArtifactReference:
    return EvidenceArtifactReference(kind, identity or kind.lower(), f"sha256:{kind.lower()}", 10, NOW, lifecycle)


def manifest(*references: EvidenceArtifactReference) -> GovernanceEvidenceManifest:
    return GovernanceEvidenceManifest(
        "1.0.0", "manifest-1", "lifecycle-1", references,
        "durable-store-1", "sha256:manifest-caller-supplied", NOW,
    )


def bundle(**changes: object) -> GovernanceEvidenceBundle:
    values = dict(
        schema_version="1.0.0", bundle_id="bundle-1", lifecycle_id="lifecycle-1",
        authorization_request_reference=ref("AUTHORIZATION_REQUEST"),
        precondition_snapshot_reference=ref("PRECONDITION_SNAPSHOT"),
        authorization_receipt_reference=ref("AUTHORIZATION_RECEIPT"),
        mutation_budget_reference=ref("MUTATION_BUDGET"),
        consumption_receipt_reference=ref("CONSUMPTION_RECEIPT"),
        execution_request_reference=ref("EXECUTION_REQUEST"),
        evidence_manifest_reference=ref("EVIDENCE_MANIFEST"),
        audit_references=(ref("AUDIT_EVENT", "audit-2"), ref("AUDIT_EVENT", "audit-1")),
        bundle_digest="sha256:bundle-caller-supplied", created_at=NOW,
    )
    values.update(changes)
    return GovernanceEvidenceBundle(**values)  # type: ignore[arg-type]


def test_artifact_reference_is_immutable_and_retains_caller_values() -> None:
    value = ref("EXECUTION_RECEIPT")
    with pytest.raises(FrozenInstanceError):
        value.digest = "other"  # type: ignore[misc]
    assert value.digest == "sha256:execution_receipt"
    assert value.created_at == NOW


def test_duplicate_artifact_identity_is_rejected() -> None:
    with pytest.raises(DuplicateEvidenceReference):
        manifest(ref("AUDIT_EVENT", "same"), ref("AUDIT_EVENT", "same"))


def test_manifest_order_is_deterministic() -> None:
    value = manifest(ref("Z_EVENT"), ref("A_EVENT"))
    assert [item.artifact_type for item in value.artifact_references] == ["A_EVENT", "Z_EVENT"]


def test_bundle_projection_is_deterministic_json_safe_and_value_free() -> None:
    value = bundle(postcondition_report_reference=ref("POSTCONDITION_REPORT"))
    first = value.to_dict()
    assert first == value.to_dict()
    assert json.loads(json.dumps(first)) == first
    names = {item.name for item in fields(value)}
    assert names.isdisjoint({"payload", "contents", "environment", "headers", "cookies", "credentials"})
    for forbidden in ("authorized", "grant_authorization", "execute"):
        assert not hasattr(value, forbidden)


def test_optional_failure_and_postcondition_references() -> None:
    empty = bundle()
    populated = bundle(
        failure_evidence_reference=ref("FAILURE_EVIDENCE"),
        postcondition_report_reference=ref("POSTCONDITION_REPORT"),
    )
    assert empty.failure_evidence_reference is None
    assert populated.postcondition_report_reference is not None


def test_mismatched_lifecycle_binding_fails_closed() -> None:
    with pytest.raises(InvalidEvidenceBundle):
        bundle(execution_request_reference=ref("EXECUTION_REQUEST", lifecycle="other"))


def test_no_file_or_hash_generation_dependency() -> None:
    import core.governance.control_plane.domain.evidence as module
    assert not hasattr(module, "open")
    assert "hashlib" not in module.__dict__
