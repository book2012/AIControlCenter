"""Static and introspective contracts for the abstract A7 governance ports."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
import inspect

import pytest

from core.governance.control_plane.domain import (
    GovernanceAuthorizationRequest,
    GovernanceEvidenceBundle,
    GovernanceEvidenceManifest,
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
    GovernancePostconditionReport,
    GovernancePreconditionSnapshot,
    PreconditionBinding,
)
from core.governance.control_plane.ports import (
    AuditPersistenceReceipt,
    ControlledExecutionPort,
    EvidencePersistencePort,
    EvidencePersistenceReceipt,
    GitReadonlyEvidencePort,
    GovernanceAuditEventRecord,
    GovernanceAuditPort,
    GovernanceAuditQuery,
    GovernanceAuditQueryResult,
    PostconditionValidationPort,
    PreconditionObservationPort,
    RuntimeIdentityObservationPort,
)


PORTS = (
    PreconditionObservationPort,
    GitReadonlyEvidencePort,
    RuntimeIdentityObservationPort,
    GovernanceAuditPort,
    EvidencePersistencePort,
    ControlledExecutionPort,
    PostconditionValidationPort,
)


def _methods(port: type) -> tuple[str, ...]:
    return tuple(
        name for name, value in vars(port).items()
        if callable(value) and not name.startswith("_")
    )


def test_all_required_interfaces_are_protocol_only() -> None:
    assert all(getattr(port, "_is_protocol", False) for port in PORTS)
    assert all(not inspect.isabstract(port) for port in PORTS)
    assert all(
        not any(
            isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            and member.name == "__init__"
            for member in ast.parse(inspect.getsource(port)).body[0].body
        )
        for port in PORTS
    )


def test_read_only_ports_are_distinct_from_controlled_execution() -> None:
    assert _methods(PreconditionObservationPort) == ("observe_preconditions",)
    assert _methods(GitReadonlyEvidencePort) == ("observe_git_evidence",)
    assert _methods(RuntimeIdentityObservationPort) == ("observe_runtime_identity",)
    assert _methods(ControlledExecutionPort) == ("invoke_once",)


def test_ports_use_frozen_domain_types_at_the_boundary() -> None:
    precondition_hints = inspect.get_annotations(
        PreconditionObservationPort.observe_preconditions, eval_str=True
    )
    assert precondition_hints == {
        "request": GovernanceAuthorizationRequest,
        "return": GovernancePreconditionSnapshot,
    }
    assert inspect.get_annotations(
        GitReadonlyEvidencePort.observe_git_evidence, eval_str=True
    )["return"] is PreconditionBinding
    execution_hints = inspect.get_annotations(ControlledExecutionPort.invoke_once, eval_str=True)
    assert execution_hints == {
        "request": GovernanceExecutionRequest,
        "return": GovernanceExecutionReceipt,
    }
    evidence_hints = inspect.get_annotations(
        EvidencePersistencePort.persist_evidence, eval_str=True
    )
    assert evidence_hints["bundle"] is GovernanceEvidenceBundle
    assert evidence_hints["manifest"] is GovernanceEvidenceManifest
    assert inspect.get_annotations(
        PostconditionValidationPort.validate_postconditions, eval_str=True
    )["return"] is GovernancePostconditionReport


def test_controlled_execution_is_one_bounded_invocation() -> None:
    assert _methods(ControlledExecutionPort) == ("invoke_once",)
    assert "remaining_count" not in inspect.signature(
        ControlledExecutionPort.invoke_once
    ).parameters


def test_no_port_exposes_authority_retry_rollback_or_widening() -> None:
    prohibited = ("authorize", "approve", "consume", "retry", "rollback", "widen", "compensate")
    names = tuple(name.lower() for port in PORTS for name in _methods(port))
    assert not any(marker in name for name in names for marker in prohibited)


def test_port_module_contains_no_concrete_side_effect_implementation() -> None:
    for port in PORTS:
        for method_name in _methods(port):
            source = inspect.getsource(getattr(port, method_name)).strip()
            assert source.endswith("...")


def test_a7_descriptors_are_immutable_and_specific() -> None:
    assert tuple(item.name for item in fields(GovernanceAuditEventRecord)) == (
        "schema_version", "event_id", "sequence", "event_type", "lifecycle_id",
        "actor", "authorization_id", "evidence_digests", "previous_hash", "event_hash",
        "timestamp",
    )
    assert tuple(item.name for item in fields(AuditPersistenceReceipt)) == (
        "event_id", "sequence", "event_hash", "persisted",
    )
    assert tuple(item.name for item in fields(GovernanceAuditQuery)) == (
        "lifecycle_id", "after_sequence", "limit",
    )
    assert tuple(item.name for item in fields(GovernanceAuditQueryResult)) == (
        "records", "query_digest",
    )
    assert tuple(item.name for item in fields(EvidencePersistenceReceipt)) == (
        "bundle_id", "manifest_id", "bundle_digest", "manifest_digest", "persisted",
    )
    receipt = EvidencePersistenceReceipt("b", "m", "bd", "md", True)
    with pytest.raises(FrozenInstanceError):
        receipt.persisted = False  # type: ignore[misc]
