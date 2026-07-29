"""Pure, immutable DPL-04C durable-audit domain contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from core.deployment.contracts import canonical_json_bytes, sha256_digest


class AuditContractError(ValueError):
    """Raised without reflecting potentially sensitive input values."""


class AuditEventType(StrEnum):
    AUTHORIZATION_ISSUED = "AUTHORIZATION_ISSUED"
    AUTHORIZATION_VALIDATED = "AUTHORIZATION_VALIDATED"
    EXECUTION_REQUESTED = "EXECUTION_REQUESTED"
    SANDBOX_TARGET_VERIFIED = "SANDBOX_TARGET_VERIFIED"
    SANDBOX_PREPARED = "SANDBOX_PREPARED"
    EXECUTION_RESULT_RECORDED = "EXECUTION_RESULT_RECORDED"
    POLICY_DENIED = "POLICY_DENIED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"


GENESIS_PREVIOUS_HASH = "GENESIS"
ALLOWED_ENVIRONMENTS = frozenset({"development", "test", "staging"})
_FORBIDDEN_KEYS = frozenset(
    {
        "api_key", "argv", "authorization_header", "command", "cookie",
        "credentials", "environment_variables", "password", "personal_data",
        "private_key", "raw_environment", "script", "secret", "shell", "token",
    }
)


def _timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise AuditContractError("invalid explicit timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AuditContractError("invalid explicit timestamp")


def _safe_key(key: str) -> None:
    normalized = key.lower()
    if normalized in _FORBIDDEN_KEYS or any(
        marker in normalized
        for marker in ("password", "secret", "token", "credential", "cookie")
    ):
        raise AuditContractError("secret-bearing or executable fields are prohibited")


def _freeze(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise AuditContractError("audit object keys must be strings")
            _safe_key(key)
            frozen[key] = _freeze(child)
        return MappingProxyType(frozen)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_freeze(child) for child in value)
    raise AuditContractError("audit values must be canonical JSON-compatible")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_plain(child) for child in value]
    return value


def _required_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AuditContractError(f"{field} must be non-empty text")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    sequence: int
    previous_event_hash: str
    event_hash: str
    recorded_at: str
    actor_identity: str
    authorization_id: str | None
    package_digest: str | None
    plan_digest: str | None
    target_identity: str | None
    environment: str
    executor_request_id: str | None
    executor_result_id: str | None
    evidence_digests: tuple[str, ...]
    policy_decision: str
    payload: Mapping[str, Any]
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, AuditEventType):
            raise AuditContractError("unknown audit event type")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise AuditContractError("sequence must be a positive integer")
        if self.environment not in ALLOWED_ENVIRONMENTS:
            raise AuditContractError("unknown privileged environment")
        if self.production_authorized is not False:
            raise AuditContractError("production authorization is prohibited")
        _timestamp(self.recorded_at)
        for field, value in (
            ("event_id", self.event_id), ("previous_event_hash", self.previous_event_hash),
            ("event_hash", self.event_hash), ("actor_identity", self.actor_identity),
            ("policy_decision", self.policy_decision),
        ):
            _required_text(value, field)
        object.__setattr__(self, "evidence_digests", tuple(sorted(set(self.evidence_digests))))
        object.__setattr__(self, "payload", _freeze(self.payload))

    def semantic(self) -> dict[str, Any]:
        return {
            "schema_version": "dpl/audit/v1",
            "event_type": self.event_type.value,
            "sequence": self.sequence,
            "previous_event_hash": self.previous_event_hash,
            "recorded_at": self.recorded_at,
            "actor_identity": self.actor_identity,
            "authorization_id": self.authorization_id,
            "package_digest": self.package_digest,
            "plan_digest": self.plan_digest,
            "target_identity": self.target_identity,
            "environment": self.environment,
            "executor_request_id": self.executor_request_id,
            "executor_result_id": self.executor_result_id,
            "evidence_digests": list(self.evidence_digests),
            "policy_decision": self.policy_decision,
            "payload": _plain(self.payload),
            "production_authorized": False,
        }

    def as_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, **self.semantic(), "event_hash": self.event_hash}


@dataclass(frozen=True, slots=True)
class AuditEnvelope:
    events: tuple[AuditEvent, ...]
    envelope_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "dpl/audit-envelope/v1",
            "events": [event.as_dict() for event in self.events],
            "envelope_digest": self.envelope_digest,
        }


@dataclass(frozen=True, slots=True)
class AuditAppendRequest:
    event: AuditEvent
    expected_previous_hash: str


@dataclass(frozen=True, slots=True)
class AuditAppendReceipt:
    event_id: str
    sequence: int
    event_hash: str
    appended: bool


@dataclass(frozen=True, slots=True)
class AuditIntegrityReport:
    valid: bool
    event_count: int
    verified_through_sequence: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuditQuery:
    event_types: tuple[AuditEventType, ...] = ()
    after_sequence: int = 0
    limit: int = 100
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_types", tuple(sorted(set(self.event_types), key=str)))
        if self.read_only is not True or self.after_sequence < 0 or not 1 <= self.limit <= 1000:
            raise AuditContractError("audit queries must be bounded and read-only")


@dataclass(frozen=True, slots=True)
class AuditQueryResult:
    events: tuple[AuditEvent, ...]
    query_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))


def create_audit_event(
    *,
    event_type: AuditEventType | str,
    sequence: int,
    previous_event_hash: str,
    recorded_at: str,
    actor_identity: str,
    environment: str,
    policy_decision: str,
    payload: Mapping[str, Any],
    authorization_id: str | None = None,
    package_digest: str | None = None,
    plan_digest: str | None = None,
    target_identity: str | None = None,
    executor_request_id: str | None = None,
    executor_result_id: str | None = None,
    evidence_digests: Sequence[str] = (),
    production_authorized: bool = False,
) -> AuditEvent:
    try:
        typed_event = AuditEventType(event_type)
    except (TypeError, ValueError) as error:
        raise AuditContractError("unknown audit event type") from error
    semantic = {
        "schema_version": "dpl/audit/v1",
        "event_type": typed_event.value,
        "sequence": sequence,
        "previous_event_hash": previous_event_hash,
        "recorded_at": recorded_at,
        "actor_identity": actor_identity,
        "authorization_id": authorization_id,
        "package_digest": package_digest,
        "plan_digest": plan_digest,
        "target_identity": target_identity,
        "environment": environment,
        "executor_request_id": executor_request_id,
        "executor_result_id": executor_result_id,
        "evidence_digests": sorted(set(evidence_digests)),
        "policy_decision": policy_decision,
        "payload": _plain(_freeze(payload)),
        "production_authorized": production_authorized,
    }
    event_id = "aud-" + sha256_digest(semantic)[7:39]
    event_hash = sha256_digest({"event_id": event_id, **semantic})
    return AuditEvent(
        event_id=event_id, event_type=typed_event, sequence=sequence,
        previous_event_hash=previous_event_hash, event_hash=event_hash,
        recorded_at=recorded_at, actor_identity=actor_identity,
        authorization_id=authorization_id, package_digest=package_digest,
        plan_digest=plan_digest, target_identity=target_identity,
        environment=environment, executor_request_id=executor_request_id,
        executor_result_id=executor_result_id, evidence_digests=tuple(evidence_digests),
        policy_decision=policy_decision, payload=payload,
        production_authorized=production_authorized,
    )


def create_audit_envelope(events: Sequence[AuditEvent]) -> AuditEnvelope:
    immutable_events = tuple(events)
    digest = sha256_digest(
        {"schema_version": "dpl/audit-envelope/v1",
         "events": [event.as_dict() for event in immutable_events]}
    )
    return AuditEnvelope(events=immutable_events, envelope_digest=digest)


def verify_audit_chain(events: Sequence[AuditEvent]) -> AuditIntegrityReport:
    values = tuple(events)
    reasons: set[str] = set()
    seen_sequences: set[int] = set()
    previous = GENESIS_PREVIOUS_HASH
    expected_sequence = 1
    verified = 0
    for event in values:
        if event.sequence in seen_sequences:
            reasons.add("DUPLICATE_SEQUENCE")
        seen_sequences.add(event.sequence)
        if event.sequence != expected_sequence:
            reasons.add("MISSING_OR_REORDERED_EVENT")
        if event.previous_event_hash != previous:
            reasons.add("BROKEN_PREVIOUS_HASH")
        semantic = event.semantic()
        expected_id = "aud-" + sha256_digest(semantic)[7:39]
        expected_hash = sha256_digest({"event_id": expected_id, **semantic})
        if event.event_id != expected_id or event.event_hash != expected_hash:
            reasons.add("MODIFIED_EVENT")
        if not reasons:
            verified = event.sequence
        previous = event.event_hash
        expected_sequence += 1
    return AuditIntegrityReport(
        valid=not reasons, event_count=len(values),
        verified_through_sequence=verified, reason_codes=tuple(sorted(reasons)),
    )


def canonical_audit_json(value: AuditEvent | AuditEnvelope) -> bytes:
    return canonical_json_bytes(value.as_dict())


__all__ = (
    "ALLOWED_ENVIRONMENTS", "GENESIS_PREVIOUS_HASH", "AuditAppendReceipt",
    "AuditAppendRequest", "AuditContractError", "AuditEnvelope", "AuditEvent",
    "AuditEventType", "AuditIntegrityReport", "AuditQuery", "AuditQueryResult",
    "canonical_audit_json", "create_audit_envelope", "create_audit_event",
    "verify_audit_chain",
)
