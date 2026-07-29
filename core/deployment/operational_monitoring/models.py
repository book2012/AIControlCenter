"""Immutable contracts for evidence-driven read-only operational monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from core.deployment.contracts import canonical_json_bytes, sha256_digest


class OperationalMonitoringError(ValueError):
    """Fail-closed monitoring contract validation error."""


class OperationalStage(StrEnum):
    PRE_ACTIVATION = "PRE_ACTIVATION"


class MonitoringDimension(StrEnum):
    CONTROL_PLANE = "CONTROL_PLANE"
    AUDIT_INTEGRITY = "AUDIT_INTEGRITY"
    AUDIT_RECOVERY = "AUDIT_RECOVERY"
    REPLAY_INTEGRITY = "REPLAY_INTEGRITY"
    REPLAY_RECOVERY = "REPLAY_RECOVERY"
    REPLAY_CONCURRENCY = "REPLAY_CONCURRENCY"
    DEPLOYMENT_READINESS = "DEPLOYMENT_READINESS"
    TEST_HEALTH = "TEST_HEALTH"
    GIT_HEALTH = "GIT_HEALTH"
    SAFETY = "SAFETY"
    DOCUMENTATION = "DOCUMENTATION"
    PRODUCTION_AUTHORIZATION = "PRODUCTION_AUTHORIZATION"


class MonitoringStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    CRITICAL = "CRITICAL"
    NOT_CONFIGURED_ALLOWED = "NOT_CONFIGURED_ALLOWED"


class MonitoringSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertCandidateStatus(StrEnum):
    CANDIDATE = "CANDIDATE"


_DIGEST_PREFIX = "sha256:"
_SAFETY_COUNTERS = (
    "operational_database_files_created",
    "monitoring_database_writes",
    "operational_audit_writes",
    "operational_replay_writes",
    "alerts_dispatched",
    "notifications_sent",
    "n8n_invocations",
    "network_requests",
    "ubuntu_changes",
    "runtime_infrastructure_commands",
    "service_restarts",
    "api_write_routes",
    "production_activations",
)


def valid_digest(value: str | None) -> bool:
    if not isinstance(value, str) or not value.startswith(_DIGEST_PREFIX):
        return False
    body = value[len(_DIGEST_PREFIX):]
    return len(body) == 64 and all(char in "0123456789abcdef" for char in body)


def _mapping(value: Mapping[str, int]) -> Mapping[str, int]:
    normalized = dict(sorted(value.items()))
    if set(normalized) != set(_SAFETY_COUNTERS):
        raise OperationalMonitoringError("required safety evidence is missing")
    if any(not isinstance(item, int) or isinstance(item, bool) or item < 0
           for item in normalized.values()):
        raise OperationalMonitoringError("safety counters must be non-negative integers")
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class OperationalMonitoringConfig:
    maximum_evidence_age_seconds: int
    audit_backup_warning_age_seconds: int
    audit_backup_critical_age_seconds: int
    audit_recovery_drill_warning_age_seconds: int
    audit_recovery_drill_critical_age_seconds: int
    replay_backup_warning_age_seconds: int
    replay_backup_critical_age_seconds: int
    replay_recovery_drill_warning_age_seconds: int
    replay_recovery_drill_critical_age_seconds: int
    maximum_tolerated_failed_tests: int = 0
    warnings_degrade: bool = True
    git_ahead_tolerance: int = 0
    git_behind_tolerance: int = 0

    def __post_init__(self) -> None:
        pairs = (
            (self.audit_backup_warning_age_seconds,
             self.audit_backup_critical_age_seconds),
            (self.audit_recovery_drill_warning_age_seconds,
             self.audit_recovery_drill_critical_age_seconds),
            (self.replay_backup_warning_age_seconds,
             self.replay_backup_critical_age_seconds),
            (self.replay_recovery_drill_warning_age_seconds,
             self.replay_recovery_drill_critical_age_seconds),
        )
        numeric = (
            self.maximum_evidence_age_seconds, self.maximum_tolerated_failed_tests,
            self.git_ahead_tolerance, self.git_behind_tolerance,
            *(item for pair in pairs for item in pair),
        )
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 0
               for item in numeric):
            raise OperationalMonitoringError("thresholds must be non-negative integers")
        if self.maximum_evidence_age_seconds == 0:
            raise OperationalMonitoringError("maximum evidence age must be positive")
        if any(critical < warning for warning, critical in pairs):
            raise OperationalMonitoringError(
                "critical threshold must be greater than or equal to warning threshold"
            )


@dataclass(frozen=True, slots=True)
class MonitoringEvidence:
    observed_at: str
    audit_inspection_status: str | None
    audit_inspection_report_id: str | None
    audit_inspection_report_digest: str | None
    audit_evidence_generated_at: str | None
    audit_schema_valid: bool | None
    audit_hash_chain_valid: bool | None
    audit_production_privacy_violations: int | None
    audit_recovery_status: str | None
    audit_recovery_report_id: str | None
    audit_recovery_report_digest: str | None
    audit_recovery_evidence_generated_at: str | None
    audit_backup_age_seconds: int | None
    audit_recovery_drill_age_seconds: int | None
    replay_inspection_status: str | None
    replay_inspection_report_id: str | None
    replay_inspection_report_digest: str | None
    replay_evidence_generated_at: str | None
    replay_schema_valid: bool | None
    replay_hash_chain_valid: bool | None
    replay_state_machine_valid: bool | None
    replay_violation_count: int | None
    replay_recovery_status: str | None
    replay_recovery_report_id: str | None
    replay_recovery_report_digest: str | None
    replay_recovery_evidence_generated_at: str | None
    replay_backup_age_seconds: int | None
    replay_recovery_drill_age_seconds: int | None
    permit_states_restored: bool | None
    replay_protection_restored: bool | None
    post_recovery_concurrency_valid: bool | None
    m2_readiness_status: str | None
    m2_readiness_report_id: str | None
    m2_readiness_report_digest: str | None
    m2_evidence_generated_at: str | None
    controlled_pilot_closeout_status: str | None
    pilot_report_id: str | None
    pilot_report_digest: str | None
    pilot_evidence_generated_at: str | None
    regression_passed: int | None
    regression_failed: int | None
    regression_deselected: int | None
    regression_warnings: int | None
    git_clean: bool | None
    git_ahead: int | None
    git_behind: int | None
    documentation_complete: bool | None
    control_plane_owner: str | None
    operational_audit_database_created: bool
    operational_replay_database_created: bool
    operational_writer_activated: bool
    operational_backup_schedule_activated: bool
    safety_counters: Mapping[str, int]
    production_authorized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "safety_counters", _mapping(self.safety_counters))

    def evidence_references(self) -> tuple[str, ...]:
        return tuple(sorted(item for item in (
            self.audit_inspection_report_id, self.audit_recovery_report_id,
            self.replay_inspection_report_id, self.replay_recovery_report_id,
            self.m2_readiness_report_id, self.pilot_report_id,
        ) if item))

    def evidence_digests(self) -> tuple[str, ...]:
        return tuple(sorted(item for item in (
            self.audit_inspection_report_digest, self.audit_recovery_report_digest,
            self.replay_inspection_report_digest, self.replay_recovery_report_digest,
            self.m2_readiness_report_digest, self.pilot_report_digest,
        ) if item))


@dataclass(frozen=True, slots=True, order=True)
class MonitoringFinding:
    dimension: MonitoringDimension
    severity: MonitoringSeverity
    reason_code: str
    summary: str

    def as_dict(self) -> dict[str, str]:
        return {
            "dimension": self.dimension.value,
            "reason_code": self.reason_code,
            "severity": self.severity.value,
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class MonitoringDecision:
    dimension: MonitoringDimension
    status: MonitoringStatus
    reason_codes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"dimension": self.dimension.value, "status": self.status.value,
                "reason_codes": list(self.reason_codes)}


@dataclass(frozen=True, slots=True)
class AlertCandidate:
    alert_candidate_id: str
    deduplication_key: str
    monitoring_snapshot_id: str
    dimension: MonitoringDimension
    severity: MonitoringSeverity
    reason_code: str
    redacted_summary: str
    evidence_references: tuple[str, ...]
    first_observed_at: str
    observed_at: str
    candidate_status: AlertCandidateStatus
    dispatch_authorized: bool
    dispatched: bool
    production_authorized: bool
    candidate_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "alert_candidate_id": self.alert_candidate_id,
            "candidate_digest": self.candidate_digest,
            "candidate_status": self.candidate_status.value,
            "deduplication_key": self.deduplication_key,
            "dimension": self.dimension.value,
            "dispatch_authorized": self.dispatch_authorized,
            "dispatched": self.dispatched,
            "evidence_references": list(self.evidence_references),
            "first_observed_at": self.first_observed_at,
            "monitoring_snapshot_id": self.monitoring_snapshot_id,
            "observed_at": self.observed_at,
            "production_authorized": self.production_authorized,
            "reason_code": self.reason_code,
            "redacted_summary": self.redacted_summary,
            "severity": self.severity.value,
        }


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    snapshot_id: str
    operational_stage: OperationalStage
    overall_status: MonitoringStatus
    observed_at: str
    evidence_ids: tuple[str, ...]
    evidence_digests: tuple[str, ...]
    dimensions: tuple[MonitoringDecision, ...]
    findings: tuple[MonitoringFinding, ...]
    restrictions: tuple[str, ...]
    alert_candidates: tuple[AlertCandidate, ...]
    safety_counters: Mapping[str, int]
    regression_summary: Mapping[str, int]
    git_summary: Mapping[str, int | bool]
    snapshot_digest: str
    writes_performed: int = 0
    alerts_dispatched: int = 0
    notifications_sent: int = 0
    production_authorized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "safety_counters",
                           MappingProxyType(dict(sorted(self.safety_counters.items()))))
        object.__setattr__(self, "regression_summary",
                           MappingProxyType(dict(sorted(self.regression_summary.items()))))
        object.__setattr__(self, "git_summary",
                           MappingProxyType(dict(sorted(self.git_summary.items()))))

    def as_dict(self) -> dict[str, Any]:
        return {
            "alert_candidates": [item.as_dict() for item in self.alert_candidates],
            "alerts_dispatched": self.alerts_dispatched,
            "dimensions": [item.as_dict() for item in self.dimensions],
            "evidence_digests": list(self.evidence_digests),
            "evidence_ids": list(self.evidence_ids),
            "findings": [item.as_dict() for item in self.findings],
            "git_summary": dict(self.git_summary),
            "notifications_sent": self.notifications_sent,
            "observed_at": self.observed_at,
            "operational_stage": self.operational_stage.value,
            "overall_status": self.overall_status.value,
            "production_authorized": self.production_authorized,
            "regression_summary": dict(self.regression_summary),
            "restrictions": list(self.restrictions),
            "safety_counters": dict(self.safety_counters),
            "snapshot_digest": self.snapshot_digest,
            "snapshot_id": self.snapshot_id,
            "writes_performed": self.writes_performed,
        }

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode("utf-8")


def digest_payload(value: Any) -> str:
    return sha256_digest(value)
