"""Pure, value-free contracts for Shopping volume identity continuity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


DATABASE_VOLUME = "ai-shopping-database"
DATABASE_DESTINATION = "/var/lib/mysql"
WORDPRESS_VOLUME = "ai-shopping-wordpress"
WORDPRESS_DESTINATION = "/var/www/html"
CANONICAL_VOLUMES = (DATABASE_VOLUME, WORDPRESS_VOLUME)
EXPECTED_DESTINATIONS = {
    DATABASE_VOLUME: DATABASE_DESTINATION,
    WORDPRESS_VOLUME: WORDPRESS_DESTINATION,
}


class ContinuityCompleteness(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    MALFORMED = "malformed"
    UNAVAILABLE = "unavailable"


class ContinuityReason(str, Enum):
    NONE = "none"
    VOLUME_ABSENT = "volume_absent"
    SOURCE_UNAVAILABLE = "source_unavailable"
    MALFORMED_EVIDENCE = "malformed_evidence"
    UNEXPECTED_VOLUME = "unexpected_volume"
    WRONG_EXPECTED_DESTINATION = "wrong_expected_destination"
    ATTACHMENT_ABSENT = "attachment_absent"
    ATTACHMENT_NOT_VOLUME = "attachment_not_volume"
    ATTACHMENT_DESTINATION_MISMATCH = "attachment_destination_mismatch"
    AMBIGUOUS_ATTACHMENT = "ambiguous_attachment"
    IDENTITY_METADATA_MISSING = "identity_metadata_missing"
    IDENTITY_METADATA_CHANGED = "identity_metadata_changed"


@dataclass(frozen=True, slots=True)
class VolumeContinuitySnapshot:
    volume_name: str
    present: bool | None
    driver: str | None
    scope: str | None
    created_at: str | None
    expected_attachment: bool | None
    expected_destination: str
    observed_destination: str | None
    attachment_type: str | None
    service: str | None
    container: str | None
    completeness: ContinuityCompleteness
    reason: ContinuityReason

    def to_json_safe(self) -> dict[str, object]:
        return {
            "volume_name": self.volume_name,
            "present": self.present,
            "driver": self.driver,
            "scope": self.scope,
            "created_at": self.created_at,
            "expected_attachment": self.expected_attachment,
            "expected_destination": self.expected_destination,
            "observed_destination": self.observed_destination,
            "attachment_type": self.attachment_type,
            "service": self.service,
            "container": self.container,
            "completeness": self.completeness.value,
            "reason": self.reason.value,
        }


@dataclass(frozen=True, slots=True)
class StorageContinuityObservation:
    volumes: tuple[VolumeContinuitySnapshot, ...]

    def to_json_safe(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "authoritative_work_item": "SHOP-SERVICE-START-01B",
            "evidence_kind": "volume_identity_observation",
            "volumes": [item.to_json_safe() for item in self.volumes],
            "content_preservation_proven": False,
            "backup_restore_proven": False,
            "mutation_authorized": False,
            "mutation_performed": False,
        }


@dataclass(frozen=True, slots=True)
class VolumeIdentityContinuityResult:
    volume_identity_continuity_proven: bool
    reasons: tuple[ContinuityReason, ...]

    def to_json_safe(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "evidence_kind": "volume_identity_continuity_comparison",
            "volume_identity_continuity_proven": self.volume_identity_continuity_proven,
            "reasons": [reason.value for reason in self.reasons],
            "content_preservation_proven": False,
            "backup_restore_proven": False,
            "recovery_authorized": False,
            "mutation_authorized": False,
            "mutation_selected": False,
        }


def _validate(observation: StorageContinuityObservation) -> tuple[ContinuityReason, ...]:
    reasons: list[ContinuityReason] = []
    by_name: dict[str, VolumeContinuitySnapshot] = {}
    for item in observation.volumes:
        if item.volume_name not in CANONICAL_VOLUMES or item.volume_name in by_name:
            reasons.append(ContinuityReason.UNEXPECTED_VOLUME)
            continue
        by_name[item.volume_name] = item
        if item.expected_destination != EXPECTED_DESTINATIONS[item.volume_name]:
            reasons.append(ContinuityReason.WRONG_EXPECTED_DESTINATION)
        if item.completeness is not ContinuityCompleteness.COMPLETE or item.reason is not ContinuityReason.NONE:
            reasons.append(item.reason if item.reason is not ContinuityReason.NONE else ContinuityReason.MALFORMED_EVIDENCE)
        if item.present is not True:
            reasons.append(ContinuityReason.VOLUME_ABSENT)
        if not all(isinstance(value, str) and value for value in (item.driver, item.scope, item.created_at)):
            reasons.append(ContinuityReason.IDENTITY_METADATA_MISSING)
        if item.expected_attachment is not True:
            reasons.append(ContinuityReason.ATTACHMENT_ABSENT)
        if item.attachment_type != "volume":
            reasons.append(ContinuityReason.ATTACHMENT_NOT_VOLUME)
        if item.observed_destination != item.expected_destination:
            reasons.append(ContinuityReason.ATTACHMENT_DESTINATION_MISMATCH)
    if set(by_name) != set(CANONICAL_VOLUMES) or len(observation.volumes) != len(CANONICAL_VOLUMES):
        reasons.append(ContinuityReason.UNEXPECTED_VOLUME)
    return tuple(dict.fromkeys(reasons))


def compare_volume_identity_continuity(
    before: StorageContinuityObservation,
    after: StorageContinuityObservation,
) -> VolumeIdentityContinuityResult:
    """Prove identity continuity only; never preservation, recovery, or authority."""
    reasons = list(_validate(before) + _validate(after))
    before_by_name = {item.volume_name: item for item in before.volumes}
    after_by_name = {item.volume_name: item for item in after.volumes}
    if not reasons:
        for name in CANONICAL_VOLUMES:
            left = before_by_name[name]
            right = after_by_name[name]
            if (left.driver, left.scope, left.created_at) != (right.driver, right.scope, right.created_at):
                reasons.append(ContinuityReason.IDENTITY_METADATA_CHANGED)
            if (left.observed_destination, left.attachment_type, left.service, left.container) != (
                right.observed_destination, right.attachment_type, right.service, right.container
            ):
                reasons.append(ContinuityReason.MALFORMED_EVIDENCE)
    unique = tuple(dict.fromkeys(reasons))
    return VolumeIdentityContinuityResult(not unique, unique)


__all__ = (
    "CANONICAL_VOLUMES", "ContinuityCompleteness", "ContinuityReason",
    "DATABASE_DESTINATION", "DATABASE_VOLUME", "EXPECTED_DESTINATIONS",
    "StorageContinuityObservation", "VolumeContinuitySnapshot",
    "VolumeIdentityContinuityResult", "WORDPRESS_DESTINATION", "WORDPRESS_VOLUME",
    "compare_volume_identity_continuity",
)
