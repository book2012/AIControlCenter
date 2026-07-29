from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.deployment.audit_contracts import (
    GENESIS_PREVIOUS_HASH,
    AuditContractError,
    AuditEventType,
    AuditQuery,
    canonical_audit_json,
    create_audit_envelope,
    create_audit_event,
    verify_audit_chain,
)
from core.deployment.policy import validate_dependency_boundaries


ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-07-29T12:00:00Z"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _event(sequence: int, previous: str, **changes):
    values = {
        "event_type": AuditEventType.EXECUTION_REQUESTED,
        "sequence": sequence,
        "previous_event_hash": previous,
        "recorded_at": STAMP,
        "actor_identity": "operator-01",
        "authorization_id": "exa-01",
        "package_digest": DIGEST_A,
        "plan_digest": DIGEST_B,
        "target_identity": "mac-sandbox-01",
        "environment": "staging",
        "executor_request_id": "exr-01",
        "evidence_digests": (DIGEST_B, DIGEST_A, DIGEST_A),
        "policy_decision": "ALLOWED_NON_PRODUCTION",
        "payload": {"z": [3, 2, 1], "a": {"reference_id": "ref-01"}},
    }
    values.update(changes)
    return create_audit_event(**values)


def test_schema_validation_immutable_input_and_query_contract() -> None:
    event = _event(1, GENESIS_PREVIOUS_HASH)
    assert event.production_authorized is False
    assert event.evidence_digests == (DIGEST_A, DIGEST_B)
    with pytest.raises(TypeError):
        event.payload["new"] = "value"
    with pytest.raises(TypeError):
        event.payload["a"]["new"] = "value"
    with pytest.raises(FrozenInstanceError):
        event.sequence = 2
    assert AuditQuery(event_types=(AuditEventType.POLICY_DENIED,)).read_only is True
    with pytest.raises(AuditContractError):
        AuditQuery(read_only=False)


def test_canonical_json_event_id_hash_and_envelope_digest_are_stable() -> None:
    first = _event(1, GENESIS_PREVIOUS_HASH)
    second = _event(
        1, GENESIS_PREVIOUS_HASH,
        payload={"a": {"reference_id": "ref-01"}, "z": [3, 2, 1]},
        evidence_digests=(DIGEST_A, DIGEST_B),
    )
    assert first == second
    assert canonical_audit_json(first) == canonical_audit_json(second)
    assert create_audit_envelope((first,)) == create_audit_envelope((second,))


def test_genesis_and_valid_hash_chain() -> None:
    first = _event(1, GENESIS_PREVIOUS_HASH)
    second = _event(
        2, first.event_hash,
        event_type=AuditEventType.SANDBOX_TARGET_VERIFIED,
        executor_request_id="exr-02",
    )
    third = _event(
        3, second.event_hash,
        event_type=AuditEventType.EXECUTION_RESULT_RECORDED,
        executor_result_id="result-01",
    )
    report = verify_audit_chain((first, second, third))
    assert report.valid
    assert report.verified_through_sequence == 3
    assert report.reason_codes == ()


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (lambda first, second: (first, replace(second, previous_event_hash=DIGEST_A)),
         "BROKEN_PREVIOUS_HASH"),
        (lambda first, second: (first, replace(second, payload={"changed": True})),
         "MODIFIED_EVENT"),
        (lambda first, second: (second, first), "MISSING_OR_REORDERED_EVENT"),
        (lambda first, second: (first, replace(second, sequence=1)),
         "DUPLICATE_SEQUENCE"),
        (lambda first, second: (first, replace(second, sequence=3)),
         "MISSING_OR_REORDERED_EVENT"),
    ],
)
def test_integrity_failures_are_detected(mutator, reason: str) -> None:
    first = _event(1, GENESIS_PREVIOUS_HASH)
    second = _event(2, first.event_hash)
    report = verify_audit_chain(mutator(first, second))
    assert not report.valid
    assert reason in report.reason_codes


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "value"},
        {"api_key": "value"},
        {"access_token": "value"},
        {"private_key": "value"},
        {"cookie": "value"},
        {"authorization_header": "value"},
        {"raw_environment": {"NAME": "value"}},
        {"command": "value"},
        {"argv": ["value"]},
        {"script": "value"},
        {"profile": {"personal_data": "unrestricted"}},
    ],
)
def test_secret_executable_and_unrestricted_personal_fields_rejected(payload) -> None:
    with pytest.raises(AuditContractError):
        _event(1, GENESIS_PREVIOUS_HASH, payload=payload)


def test_production_unknown_environment_and_event_type_rejected() -> None:
    with pytest.raises(AuditContractError):
        _event(1, GENESIS_PREVIOUS_HASH, production_authorized=True)
    with pytest.raises(AuditContractError):
        _event(1, GENESIS_PREVIOUS_HASH, environment="production")
    with pytest.raises(AuditContractError):
        _event(1, GENESIS_PREVIOUS_HASH, event_type="PRODUCTION_SUCCEEDED")


def test_audit_zone_has_no_adapter_persistence_network_command_or_worker_dependency(
    tmp_path: Path,
) -> None:
    forbidden = {
        "sqlite3", "subprocess", "socket", "requests", "paramiko",
        "core.api", "core.worker", "core.deployment.sandbox_adapter",
    }
    sources = tuple((ROOT / "core/deployment/audit_contracts").glob("*.py"))
    assert sources
    for source in sources:
        text = source.read_text("utf-8")
        tree = ast.parse(text)
        imports = {
            node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        }
        assert not any(
            item == prefix or item.startswith(prefix + ".")
            for item in imports for prefix in forbidden
        )
        assert not any(marker in text for marker in (".db", ".sqlite", "connect("))
    assert not list(tmp_path.iterdir())
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    assert report["production_authorized"] is False


def test_no_api_write_route_was_added() -> None:
    audit_sources = list((ROOT / "core/api").rglob("*audit*.py"))
    assert not any("AuditAppend" in source.read_text("utf-8") for source in audit_sources)
