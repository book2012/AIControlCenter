from __future__ import annotations

from dataclasses import fields
import inspect
import json

import pytest

from core.continuity_witness.contracts import CheckpointPayload, HistoryCoverage, ImmutableHistoryObservation, StoredCheckpoint, TransitionIntent, WitnessCheckpointSigningEnvelope
from core.continuity_witness.domain import ApprovalClaimState, ContinuityHostId, IdentityEvaluationId, LifecycleOperation, LifecycleOperationId, fresh_mda_required, mutation_post_retry_allowed
from core.continuity_witness.json_contracts import CanonicalizationError, ContractValidationError, canonical_signed_bytes, decode_base64url, encode_base64url
from core.continuity_witness import ports

UUID7_A = "01890f3c-4b2a-7cc1-8c00-000000000001"
UUID7_B = "01890f3c-4b2a-7cc1-8c00-000000000002"
UUID7_C = "01890f3c-4b2a-7cc1-8c00-000000000003"
DIGEST = encode_base64url(b"d" * 32)


def intent(operation=LifecycleOperation.GENESIS_ENROLLMENT):
    kwargs = dict(operation_id=LifecycleOperationId(UUID7_A), evaluation_id=IdentityEvaluationId(UUID7_B), operation_type=operation,
                  expected_continuity_host_id=None, expected_predecessor_continuity_host_id=None,
                  expected_record_generation=None, validated_hardware_evidence_binding_digest=DIGEST)
    if operation in {LifecycleOperation.RECOVERY, LifecycleOperation.DECOMMISSION}:
        kwargs.update(expected_continuity_host_id=ContinuityHostId(UUID7_C), expected_record_generation=4)
    if operation is LifecycleOperation.MIGRATION:
        kwargs.update(expected_predecessor_continuity_host_id=ContinuityHostId(UUID7_C), expected_record_generation=4)
    if operation is LifecycleOperation.DECOMMISSION:
        kwargs["validated_hardware_evidence_binding_digest"] = None
    return TransitionIntent(**kwargs)


def test_transition_intent_digest_is_deterministic_and_excludes_stage_b_results():
    first, second = intent(), intent()
    assert first.expected_transition_intent_digest == second.expected_transition_intent_digest
    encoded = json.dumps(first.as_dict(), sort_keys=True)
    assert "resulting_transition_digest" not in encoded and "transition_id" not in encoded


def test_approval_cannot_bind_resulting_transition_digest():
    stage_b_result_fields = {
        "resulting_transition_digest", "resulting_transition_digests", "transition_id",
    }
    constructor_fields = {field.name for field in fields(TransitionIntent)}
    assert stage_b_result_fields.isdisjoint(constructor_fields)
    assert stage_b_result_fields.isdisjoint(intent().as_dict())


def test_float_and_padded_base64url_are_rejected():
    with pytest.raises(CanonicalizationError): canonical_signed_bytes({"schema_version":"1", "domain":"X", "n":1.5})
    with pytest.raises(ContractValidationError): decode_base64url("ZA==")


def test_oversized_signed_envelope_is_rejected():
    with pytest.raises(ContractValidationError): canonical_signed_bytes({"schema_version":"1", "domain":"X", "value":"x"*4096})


def test_checkpoint_object_digest_is_publication_metadata_not_hashed_content():
    payload = CheckpointPayload({"schema_version":"1", "domain":"CONTINUITY_CHECKPOINT_PAYLOAD", "checkpoint_id":UUID7_A})
    envelope = WitnessCheckpointSigningEnvelope({"schema_version":"1", "domain":"WITNESS_PROTOCOL_EVIDENCE", "evidence_type":"IMMUTABLE_CONTINUITY_CHECKPOINT", "application_payload_digest":payload.application_payload_digest, "signature":encode_base64url(b"s"*64)})
    stored = StoredCheckpoint(payload, envelope)
    assert b"object_digest" not in stored.canonical_bytes
    assert len(decode_base64url(stored.object_digest)) == 32


def test_checkpoint_envelope_must_bind_application_payload_digest():
    payload = CheckpointPayload({"schema_version":"1", "domain":"CONTINUITY_CHECKPOINT_PAYLOAD", "checkpoint_id":UUID7_A})
    envelope = WitnessCheckpointSigningEnvelope({"schema_version":"1", "domain":"WITNESS_PROTOCOL_EVIDENCE", "evidence_type":"IMMUTABLE_CONTINUITY_CHECKPOINT", "application_payload_digest":DIGEST, "signature":encode_base64url(b"s"*64)})
    with pytest.raises(ValueError, match="application payload digest"):
        StoredCheckpoint(payload, envelope)


@pytest.mark.parametrize("signature_size", [0, 63, 65])
def test_checkpoint_envelope_rejects_non_ed25519_signature_lengths(signature_size):
    with pytest.raises(ValueError, match="exactly 64 bytes"):
        WitnessCheckpointSigningEnvelope({
            "schema_version": "1", "domain": "WITNESS_PROTOCOL_EVIDENCE",
            "evidence_type": "IMMUTABLE_CONTINUITY_CHECKPOINT",
            "application_payload_digest": DIGEST,
            "signature": encode_base64url(b"s" * signature_size),
        })


def test_checkpoint_envelope_accepts_64_byte_ed25519_signature():
    envelope = WitnessCheckpointSigningEnvelope({
        "schema_version": "1", "domain": "WITNESS_PROTOCOL_EVIDENCE",
        "evidence_type": "IMMUTABLE_CONTINUITY_CHECKPOINT",
        "application_payload_digest": DIGEST,
        "signature": encode_base64url(b"s" * 64),
    })
    assert len(decode_base64url(envelope.as_dict()["signature"])) == 64


@pytest.mark.parametrize("observation", [
    ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, True, delete_marker_observed=True),
    ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, True, latest_key_not_found=True),
    ImmutableHistoryObservation(HistoryCoverage.UNAVAILABLE, True),
])
def test_incomplete_current_key_evidence_never_proves_absence(observation):
    assert not observation.proves_historical_absence
    assert not hasattr(observation, "genesis_eligible")


def test_complete_history_absence_is_evidence_without_genesis_authority():
    observation = ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, True)
    assert observation.proves_historical_absence
    assert not hasattr(observation, "genesis_eligible")


@pytest.mark.parametrize("coverage", ["COMPLETE_ABSENT", "ARBITRARY", None])
def test_history_coverage_rejects_values_outside_closed_enum(coverage):
    with pytest.raises(ValueError, match="closed HistoryCoverage"):
        ImmutableHistoryObservation(coverage, True)


@pytest.mark.parametrize("field_name", [
    "version_aware", "delete_marker_observed", "latest_key_not_found",
])
@pytest.mark.parametrize("invalid_bool", [0, 1, None, "true"])
def test_history_observation_requires_exact_bool_fields(field_name, invalid_bool):
    kwargs = {
        "coverage": HistoryCoverage.COMPLETE_ABSENT,
        "version_aware": True,
        "delete_marker_observed": False,
        "latest_key_not_found": False,
    }
    kwargs[field_name] = invalid_bool
    with pytest.raises(ValueError, match=f"{field_name} must be exactly bool"):
        ImmutableHistoryObservation(**kwargs)


def test_claim_consumption_and_retry_invariants():
    assert not ApprovalClaimState.DURABLY_CLAIMED.reusable
    assert not ApprovalClaimState.COMMITTED.reusable
    assert not ApprovalClaimState.FAILED_CONSUMED.reusable
    assert not ApprovalClaimState.UNCERTAIN_CONSUMED.reusable
    assert not mutation_post_retry_allowed(outcome_ambiguous=True)
    assert ports.LifecycleApprovalVerifier.__dict__.get("sign") is None


@pytest.mark.parametrize(("operation", "required"), [
    (LifecycleOperation.DECOMMISSION, False), (LifecycleOperation.GENESIS_ENROLLMENT, True),
    (LifecycleOperation.RECOVERY, True), (LifecycleOperation.MIGRATION, True),
])
def test_fresh_mda_precedence(operation, required):
    assert fresh_mda_required(operation) is required
    assert intent(operation).as_dict()["required_postconditions"]["require_fresh_mda"] is required


def test_hardware_privacy_port_and_no_infrastructure_or_ubuntu_role():
    source = inspect.getsource(ports)
    lowered = source.lower()
    assert "boto3" not in lowered and "psycopg" not in lowered and "postgresql" not in lowered and "mdm sdk" not in lowered
    assert "url" not in ports.HardwareIndexPort.index_validated_hardware.__annotations__
    assert ports.CONTINUITY_WITNESS_MDA_TRANSPORT == "DEVICE_INFORMATION"
    assert ports.MAC_MINI_M4_IS_SOLE_CONTROL_PLANE
    assert not ports.CONTINUITY_WITNESS_IS_SECOND_CONTROL_PLANE
    assert not ports.UBUNTU_IMPLEMENTATION_ROLE


def test_external_atomicity_contract_is_read_only_reconciliation_capable():
    assert hasattr(ports.TransactionStorePort, "get_operation")
    assert hasattr(ports.ImmutableHistoryPort, "get_checkpoint")
    assert not mutation_post_retry_allowed(outcome_ambiguous=True)
