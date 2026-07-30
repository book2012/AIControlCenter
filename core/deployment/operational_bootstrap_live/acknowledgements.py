"""Typed full-evidence to executor-warning acknowledgement projection."""

from __future__ import annotations

from .models import (
    WARNING_RESTRICTION_IDENTIFIER,
    ControlledLivePermitCompatibilityReport,
    ControlledOperationalBootstrapError,
    ControlledOperationalBootstrapRequest,
    ControlledRestrictionAcknowledgement,
    ControlledWarningAcknowledgement,
    ControlledWarningAcknowledgementProjection,
    canonical_digest,
)


class ControlledWarningAcknowledgementProjector:
    """Select the warning class semantically; never truncate by position."""

    def project(
            self, *,
            evidence: tuple[ControlledRestrictionAcknowledgement, ...],
            request: ControlledOperationalBootstrapRequest,
            ) -> ControlledWarningAcknowledgementProjection:
        if not isinstance(evidence, tuple) or any(
                not isinstance(item, ControlledRestrictionAcknowledgement)
                for item in evidence):
            raise ControlledOperationalBootstrapError(
                "TYPED_RESTRICTION_ACKNOWLEDGEMENTS_REQUIRED")
        if not evidence:
            raise ControlledOperationalBootstrapError(
                "WARNING_ACKNOWLEDGEMENT_EVIDENCE_MISSING")
        warning = tuple(item for item in evidence
                        if item.restriction_identifier
                        == WARNING_RESTRICTION_IDENTIFIER)
        required = {
            request.operator_identity, request.independent_approver_identity}
        identities = [item.acknowledging_identity for item in warning]
        if len(warning) != 2:
            raise ControlledOperationalBootstrapError(
                "EXACT_WARNING_ACKNOWLEDGEMENT_PAIR_REQUIRED")
        if len(set(identities)) != len(identities):
            raise ControlledOperationalBootstrapError(
                "DUPLICATE_WARNING_ACKNOWLEDGEMENT_IDENTITY")
        if set(identities) != required:
            raise ControlledOperationalBootstrapError(
                "WARNING_ACKNOWLEDGEMENT_IDENTITY_PAIR_INVALID")
        if request.operator_identity == request.independent_approver_identity:
            raise ControlledOperationalBootstrapError(
                "INDEPENDENT_WARNING_ACKNOWLEDGEMENT_REQUIRED")
        projected = tuple(sorted((ControlledWarningAcknowledgement(
            item.restriction_identifier, item.acknowledging_identity,
            item.acknowledgement_digest) for item in warning),
            key=lambda item: item.acknowledgement_digest))
        full = tuple(sorted(evidence))
        return ControlledWarningAcknowledgementProjection(
            full, projected,
            canonical_digest([item.as_dict() for item in full]),
            canonical_digest([item.as_dict() for item in projected]))


class ControlledLivePermitCompatibilityValidator:
    """Pre-issuance proof that the executor-facing permit shape is acceptable."""

    def validate(
            self, *,
            request: ControlledOperationalBootstrapRequest,
            projection: ControlledWarningAcknowledgementProjection,
            ) -> ControlledLivePermitCompatibilityReport:
        if not isinstance(projection, ControlledWarningAcknowledgementProjection):
            raise ControlledOperationalBootstrapError(
                "TYPED_WARNING_PROJECTION_REQUIRED")
        expected = ControlledWarningAcknowledgementProjector().project(
            evidence=request.restriction_acknowledgements, request=request)
        if expected != projection:
            raise ControlledOperationalBootstrapError(
                "WARNING_PROJECTION_BINDING_INVALID")
        content = {
            "full_restriction_acknowledgement_digest":
                projection.full_restriction_acknowledgement_digest,
            "warning_acknowledgement_digest":
                projection.warning_acknowledgement_digest,
            "compatible": True,
        }
        return ControlledLivePermitCompatibilityReport(
            projection, True, canonical_digest(content))

    def validate_permit(
            self, *, request: ControlledOperationalBootstrapRequest,
            permit, report: ControlledLivePermitCompatibilityReport) -> None:
        if not isinstance(report, ControlledLivePermitCompatibilityReport):
            raise ControlledOperationalBootstrapError(
                "TYPED_COMPATIBILITY_REPORT_REQUIRED")
        projected = report.projection
        if (tuple(permit.warning_acknowledgements) != tuple(sorted(
                item.acknowledgement_digest
                for item in projected.warning_acknowledgements))
                or permit.full_restriction_acknowledgement_digest
                != projected.full_restriction_acknowledgement_digest
                or permit.warning_acknowledgement_digest
                != projected.warning_acknowledgement_digest):
            raise ControlledOperationalBootstrapError(
                "LIVE_PERMIT_ACKNOWLEDGEMENT_BINDING_INVALID")
        permit.validate_for(request, permit.issued_at)
