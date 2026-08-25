"""Content-free canonical codec for acquisition authorization consumption."""

from hashlib import sha256
import json

from core.secrets.mariadb_continuity_protected_evidence_acquisition_authorization import (
    ProtectedEvidenceAcquisitionAuthorization,
)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def digest_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def binding_document(value: ProtectedEvidenceAcquisitionAuthorization) -> dict[str, object]:
    if type(value) is not ProtectedEvidenceAcquisitionAuthorization:
        raise TypeError("authorization type is invalid")
    return {
        "codec_version": 1,
        "authorization_id": value.authorization_id,
        "acquisition_request_id": value.acquisition_request_id,
        "fixed_source_slot_identity": value.fixed_source_slot_identity.value,
        "concrete_source_location_identity": value.concrete_source_location_identity.value,
        "leaf_basename": value.leaf_basename,
        "concrete_leaf_path": value.concrete_leaf_path,
        "maximum_acquisition_attempts": value.maximum_acquisition_attempts,
    }


def encode_binding(value: ProtectedEvidenceAcquisitionAuthorization) -> tuple[str, str]:
    encoded = canonical_json(binding_document(value))
    return encoded, digest_text(encoded)


def encode_committed(binding_digest: str) -> tuple[str, str]:
    encoded = canonical_json({"barrier_state": "COMMITTED", "binding_digest": binding_digest, "codec_version": 1})
    return encoded, digest_text(encoded)


__all__ = ("binding_document", "canonical_json", "digest_text", "encode_binding", "encode_committed")
