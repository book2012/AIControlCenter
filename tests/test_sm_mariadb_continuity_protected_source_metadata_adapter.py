from concurrent.futures import ThreadPoolExecutor

import pytest

from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    ProtectedExternalEvidenceConcreteSourceLocationIdentity as SourceIdentity,
)

from core.secrets.mariadb_continuity_protected_source_metadata import (
    MetadataInspectionOutcome as Outcome,
    MetadataInspectionReason as Reason,
    MetadataEvidenceProvenance as Provenance,
    ProtectedSourceMetadataInspectionRequest,
)
from core.secrets.mariadb_continuity_protected_source_metadata_port import (
    InspectionAuthorizationError,
    ProtectedSourceMetadataInspectionCapability,
)
from ops.macos.shopping.mariadb_continuity_protected_source_metadata_adapter import (
    MacProtectedSourceMetadataAdapter,
    _BoundMetadataObservation,
    _InertObservationMarker,
)
from ops.macos.shopping.mariadb_continuity_protected_source_metadata_composition import (
    _compose_inert_test_metadata_inspector,
    _issue_inert_test_inspection_capability,
)

def invoke(value):
    request = ProtectedSourceMetadataInspectionRequest.canonical(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    adapter = _compose_inert_test_metadata_inspector(value)
    result = adapter.inspect_once(
        request, _issue_inert_test_inspection_capability(request)
    )
    return result


@pytest.mark.parametrize("reason,outcome", [(r, {
    Reason.METADATA_SAFE_AND_STABLY_BOUND: Outcome.SAFE_BOUND,
    Reason.SOURCE_ABSENT: Outcome.ABSENT, Reason.PARENT_ABSENT: Outcome.ABSENT,
    Reason.SYMLINK_REJECTED: Outcome.UNSAFE, Reason.WRONG_FILE_TYPE: Outcome.UNSAFE,
    Reason.PARENT_MODE_MISMATCH: Outcome.UNSAFE, Reason.LEAF_PERMISSIONS_TOO_BROAD: Outcome.UNSAFE,
    Reason.PARENT_UID_GID_MISMATCH: Outcome.UNSAFE, Reason.LEAF_UID_GID_MISMATCH: Outcome.UNSAFE,
    Reason.INODE_DEVICE_INSTABILITY: Outcome.UNCERTAIN, Reason.PATH_REPLACEMENT_RACE: Outcome.UNCERTAIN,
    Reason.METADATA_ACCESS_FAILURE: Outcome.UNAVAILABLE, Reason.AMBIGUOUS_METADATA_RESULT: Outcome.UNCERTAIN,
}[r]) for r in Reason])
def test_classifies_every_closed_reason(reason, outcome) -> None:
    result = invoke(_BoundMetadataObservation(reason))
    assert (result.reason, result.outcome) == (reason, outcome)
    assert result.provenance is Provenance.INERT_TEST_CLASSIFICATION
    assert result.is_operational_evidence is False


def test_consumed_before_exception_and_no_retry_or_reuse() -> None:
    request = ProtectedSourceMetadataInspectionRequest.canonical(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    capability = _issue_inert_test_inspection_capability(request)
    adapter = _compose_inert_test_metadata_inspector(_InertObservationMarker.FAILURE)
    assert adapter.inspect_once(request, capability).reason is Reason.METADATA_ACCESS_FAILURE
    with pytest.raises(InspectionAuthorizationError, match="already"):
        adapter.inspect_once(request, capability)


def test_concurrent_consumption_is_exactly_once() -> None:
    request = ProtectedSourceMetadataInspectionRequest.canonical(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    capability = _issue_inert_test_inspection_capability(request)
    adapter = _compose_inert_test_metadata_inspector(_BoundMetadataObservation(Reason.SOURCE_ABSENT))
    def call():
        try: return adapter.inspect_once(request, capability).outcome
        except InspectionAuthorizationError: return "CONSUMED"
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: call(), range(8)))
    assert results.count(Outcome.ABSENT) == 1
    assert results.count("CONSUMED") == 7


def test_capability_is_closed_and_adapter_has_no_path_api() -> None:
    request = ProtectedSourceMetadataInspectionRequest.canonical(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    with pytest.raises(InspectionAuthorizationError):
        ProtectedSourceMetadataInspectionCapability(request)
    with pytest.raises(TypeError, match="direct"):
        MacProtectedSourceMetadataAdapter(object())
    assert MacProtectedSourceMetadataAdapter.inspect_once.__code__.co_varnames[:3] == ("self", "request", "capability")


def test_ambiguous_fake_result_fails_closed() -> None:
    result = invoke(_InertObservationMarker.AMBIGUOUS)
    assert (result.outcome, result.reason) == (Outcome.UNCERTAIN, Reason.AMBIGUOUS_METADATA_RESULT)


def test_cross_source_capability_is_rejected_before_observation() -> None:
    source_a, source_b = list(SourceIdentity)[:2]
    request_a = ProtectedSourceMetadataInspectionRequest.canonical(source_a)
    request_b = ProtectedSourceMetadataInspectionRequest.canonical(source_b)
    capability = _issue_inert_test_inspection_capability(request_a)
    adapter = _compose_inert_test_metadata_inspector(_BoundMetadataObservation(Reason.SOURCE_ABSENT))
    with pytest.raises(InspectionAuthorizationError, match="another request"):
        adapter.inspect_once(request_b, capability)
    assert adapter.inspect_once(request_a, capability).outcome is Outcome.ABSENT


def test_same_source_different_request_is_rejected_without_consumption() -> None:
    source = SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION
    request_a = ProtectedSourceMetadataInspectionRequest.canonical(source)
    request_b = ProtectedSourceMetadataInspectionRequest.canonical(source)
    assert request_a is not request_b
    assert request_a == request_b
    capability = _issue_inert_test_inspection_capability(request_a)
    adapter = _compose_inert_test_metadata_inspector(
        _BoundMetadataObservation(Reason.SOURCE_ABSENT)
    )
    with pytest.raises(InspectionAuthorizationError, match="another request"):
        adapter.inspect_once(request_b, capability)
    assert adapter.inspect_once(request_a, capability).outcome is Outcome.ABSENT
    with pytest.raises(InspectionAuthorizationError, match="already"):
        adapter.inspect_once(request_a, capability)


def test_callback_path_and_arbitrary_source_injection_are_rejected() -> None:
    for payload in (lambda: None, object(), "/tmp/source"):
        with pytest.raises(TypeError, match="closed inert"):
            _compose_inert_test_metadata_inspector(payload)
