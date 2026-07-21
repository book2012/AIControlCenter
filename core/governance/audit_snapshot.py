"""Canonical immutable model-governance audit snapshots."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"

_ALLOWED_SEVERITIES = frozenset(
    {
        "INFO",
        "WARNING",
        "CRITICAL",
    }
)

_GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_RELEASE_PATTERN = re.compile(r"^[0-9a-f]{12}$")
_RFC3339_UTC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,6})?Z$"
)


class AuditSnapshotError(ValueError):
    """Raised when an audit snapshot violates its domain contract."""


def _reject_floating_point_values(
    value: Any,
    path: str = "$",
) -> None:
    if isinstance(value, float):
        raise AuditSnapshotError(
            f"floating-point value is not allowed at {path}"
        )

    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AuditSnapshotError(
                    f"JSON object key must be a string at {path}"
                )

            _reject_floating_point_values(
                item,
                f"{path}.{key}",
            )

        return

    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_floating_point_values(
                item,
                f"{path}[{index}]",
            )

        return

    if value is None or isinstance(
        value,
        (str, int, bool),
    ):
        return

    raise AuditSnapshotError(
        f"unsupported JSON value at {path}: "
        f"{type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value deterministically."""

    _reject_floating_point_values(value)

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise AuditSnapshotError(
            "value cannot be serialized as canonical JSON"
        ) from error


def validate_rfc3339_utc(value: str) -> str:
    """Validate and return an RFC3339 UTC timestamp."""

    if not isinstance(value, str):
        raise AuditSnapshotError(
            "captured_at must be a string"
        )

    if _RFC3339_UTC_PATTERN.fullmatch(value) is None:
        raise AuditSnapshotError(
            "captured_at must be RFC3339 UTC with Z suffix"
        )

    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00"
        )
    except ValueError as error:
        raise AuditSnapshotError(
            "captured_at is not a valid calendar timestamp"
        ) from error

    if parsed.tzinfo is None:
        raise AuditSnapshotError(
            "captured_at must be timezone-aware"
        )

    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise AuditSnapshotError(
            "captured_at must use UTC"
        )

    return value


def _validate_non_negative_integer(
    value: Any,
    field: str,
) -> int:
    if isinstance(value, bool):
        raise AuditSnapshotError(
            f"{field} must be a non-negative integer"
        )

    if not isinstance(value, int) or value < 0:
        raise AuditSnapshotError(
            f"{field} must be a non-negative integer"
        )

    return value


@dataclass(frozen=True)
class GovernanceSummary:
    """Immutable summary of a governance evaluation."""

    severity: str
    approved_count: int
    observed_count: int
    compliant_count: int
    violation_count: int
    unapproved_count: int
    missing_count: int
    digest_mismatch_count: int
    resource_policy_violation_count: int

    def __post_init__(self) -> None:
        if self.severity not in _ALLOWED_SEVERITIES:
            raise AuditSnapshotError(
                "severity must be INFO, WARNING, or CRITICAL"
            )

        fields = (
            "approved_count",
            "observed_count",
            "compliant_count",
            "violation_count",
            "unapproved_count",
            "missing_count",
            "digest_mismatch_count",
            "resource_policy_violation_count",
        )

        for field in fields:
            _validate_non_negative_integer(
                getattr(self, field),
                field,
            )

        categorized_violations = (
            self.unapproved_count
            + self.missing_count
            + self.digest_mismatch_count
            + self.resource_policy_violation_count
        )

        if categorized_violations != self.violation_count:
            raise AuditSnapshotError(
                "violation_count must equal categorized "
                "violation counts"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "approved_count": self.approved_count,
            "observed_count": self.observed_count,
            "compliant_count": self.compliant_count,
            "violation_count": self.violation_count,
            "unapproved_count": self.unapproved_count,
            "missing_count": self.missing_count,
            "digest_mismatch_count":
                self.digest_mismatch_count,
            "resource_policy_violation_count":
                self.resource_policy_violation_count,
        }

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
    ) -> GovernanceSummary:
        if not isinstance(payload, Mapping):
            raise AuditSnapshotError(
                "summary must be an object"
            )

        try:
            return cls(
                severity=payload["severity"],
                approved_count=payload["approved_count"],
                observed_count=payload["observed_count"],
                compliant_count=payload["compliant_count"],
                violation_count=payload["violation_count"],
                unapproved_count=payload["unapproved_count"],
                missing_count=payload["missing_count"],
                digest_mismatch_count=(
                    payload["digest_mismatch_count"]
                ),
                resource_policy_violation_count=(
                    payload[
                        "resource_policy_violation_count"
                    ]
                ),
            )
        except KeyError as error:
            raise AuditSnapshotError(
                f"missing summary field: {error.args[0]}"
            ) from error


@dataclass(frozen=True)
class AuditSnapshot:
    """Immutable canonical model-governance audit snapshot."""

    snapshot_id: str
    captured_at: str
    source_commit: str
    runtime_release: str
    governance_json: str
    summary: GovernanceSummary

    @staticmethod
    def _validate_source_commit(value: str) -> str:
        if (
            not isinstance(value, str)
            or _GIT_SHA_PATTERN.fullmatch(value) is None
        ):
            raise AuditSnapshotError(
                "source_commit must be a 40-character "
                "lowercase hexadecimal Git SHA"
            )

        return value

    @staticmethod
    def _validate_runtime_release(value: str) -> str:
        if (
            not isinstance(value, str)
            or _RELEASE_PATTERN.fullmatch(value) is None
        ):
            raise AuditSnapshotError(
                "runtime_release must be a 12-character "
                "lowercase hexadecimal release ID"
            )

        return value

    @staticmethod
    def _identity_document(
        *,
        captured_at: str,
        source_commit: str,
        runtime_release: str,
        governance: Mapping[str, Any],
        summary: GovernanceSummary,
    ) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "captured_at": captured_at,
            "source_commit": source_commit,
            "runtime_release": runtime_release,
            "governance": dict(governance),
            "summary": summary.to_dict(),
        }

    @classmethod
    def create(
        cls,
        *,
        captured_at: str,
        source_commit: str,
        runtime_release: str,
        governance: Mapping[str, Any],
        summary: GovernanceSummary,
    ) -> AuditSnapshot:
        captured_at = validate_rfc3339_utc(captured_at)
        source_commit = cls._validate_source_commit(
            source_commit
        )
        runtime_release = cls._validate_runtime_release(
            runtime_release
        )

        if not isinstance(governance, Mapping):
            raise AuditSnapshotError(
                "governance must be an object"
            )

        governance_document = dict(governance)
        governance_json = canonical_json(
            governance_document
        )

        identity = cls._identity_document(
            captured_at=captured_at,
            source_commit=source_commit,
            runtime_release=runtime_release,
            governance=governance_document,
            summary=summary,
        )

        snapshot_id = hashlib.sha256(
            canonical_json(identity).encode("utf-8")
        ).hexdigest()

        return cls(
            snapshot_id=snapshot_id,
            captured_at=captured_at,
            source_commit=source_commit,
            runtime_release=runtime_release,
            governance_json=governance_json,
            summary=summary,
        )

    @property
    def governance(self) -> dict[str, Any]:
        payload = json.loads(self.governance_json)

        if not isinstance(payload, dict):
            raise AuditSnapshotError(
                "stored governance document is invalid"
            )

        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at,
            "source_commit": self.source_commit,
            "runtime_release": self.runtime_release,
            "governance": self.governance,
            "summary": self.summary.to_dict(),
        }

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
    ) -> AuditSnapshot:
        if not isinstance(payload, Mapping):
            raise AuditSnapshotError(
                "snapshot must be an object"
            )

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise AuditSnapshotError(
                "unsupported audit snapshot schema_version"
            )

        try:
            supplied_snapshot_id = payload["snapshot_id"]

            snapshot = cls.create(
                captured_at=payload["captured_at"],
                source_commit=payload["source_commit"],
                runtime_release=payload["runtime_release"],
                governance=payload["governance"],
                summary=GovernanceSummary.from_dict(
                    payload["summary"]
                ),
            )
        except KeyError as error:
            raise AuditSnapshotError(
                f"missing snapshot field: {error.args[0]}"
            ) from error

        if supplied_snapshot_id != snapshot.snapshot_id:
            raise AuditSnapshotError(
                "snapshot_id does not match canonical content"
            )

        return snapshot
