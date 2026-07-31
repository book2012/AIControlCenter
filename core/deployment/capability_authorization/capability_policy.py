"""Closed M4-A2 capability and restriction policy."""

from __future__ import annotations

from datetime import timedelta

from core.deployment.controlled_activation_architecture import (
    ControlledActivationCapability,
)

from .models import CapabilityAuthorizationRestriction


MAXIMUM_AUTHORIZATION_TTL = timedelta(hours=1)

REQUIRED_RESTRICTIONS = tuple(
    field
    for field in CapabilityAuthorizationRestriction.__dataclass_fields__
)

CAPABILITY_REQUIRED_RESTRICTIONS = {
    ControlledActivationCapability.AUDIT_WRITER: (
        "independent_approval_required",
        "single_use_required",
        "atomic_claim_required",
        "rollback_evidence_required",
        "production_denied",
        "ubuntu_denied",
    ),
    ControlledActivationCapability.REPLAY_WRITER: (
        "independent_approval_required",
        "single_use_required",
        "atomic_claim_required",
        "rollback_evidence_required",
        "production_denied",
        "ubuntu_denied",
    ),
    ControlledActivationCapability.MONITORING_RUNTIME: (
        "independent_approval_required",
        "evidence_required",
        "monitoring_does_not_authorize_alert_dispatch",
        "production_denied",
        "ubuntu_denied",
    ),
    ControlledActivationCapability.ALERT_DISPATCH: (
        "independent_approval_required",
        "dependency_does_not_constitute_authorization",
        "alert_dispatch_does_not_authorize_external_notification",
        "production_denied",
        "ubuntu_denied",
    ),
    ControlledActivationCapability.EXTERNAL_NOTIFICATION: (
        "independent_approval_required",
        "dependency_does_not_constitute_authorization",
        "external_endpoint_details_excluded",
        "production_denied",
        "ubuntu_denied",
    ),
}

DEPENDENCY_CAPABILITY = {
    ControlledActivationCapability.ALERT_DISPATCH: (
        ControlledActivationCapability.MONITORING_RUNTIME
    ),
    ControlledActivationCapability.EXTERNAL_NOTIFICATION: (
        ControlledActivationCapability.ALERT_DISPATCH
    ),
}
