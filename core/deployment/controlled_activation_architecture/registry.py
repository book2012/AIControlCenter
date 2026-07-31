"""Closed, canonical M4-A1 capability registry."""

from __future__ import annotations

from .models import (
    ControlledActivationCapability,
    ControlledActivationCapabilityDefinition,
    ControlledActivationState,
)


def _definition(
    capability: ControlledActivationCapability,
    risk: str,
    side_effect: str,
    dependencies: tuple[ControlledActivationCapability, ...] = (),
    health: tuple[str, ...] = (),
) -> ControlledActivationCapabilityDefinition:
    return ControlledActivationCapabilityDefinition(
        identifier=capability,
        control_plane_owner="AIControlCenter",
        default_state=ControlledActivationState.INACTIVE,
        default_authorized=False,
        risk_classification=risk,
        requires_independent_approval=True,
        requires_single_use_permit=True,
        requires_atomic_claim=True,
        requires_rollback_evidence=True,
        production_eligible=False,
        ubuntu_eligible=False,
        external_side_effect_classification=side_effect,
        dependency_requirements=dependencies,
        read_only_health_dependencies=health,
    )


CAPABILITY_REGISTRY = (
    _definition(ControlledActivationCapability.AUDIT_WRITER, "HIGH", "LOCAL_WRITE"),
    _definition(ControlledActivationCapability.REPLAY_WRITER, "HIGH", "LOCAL_WRITE"),
    _definition(
        ControlledActivationCapability.MONITORING_RUNTIME,
        "MEDIUM",
        "LOCAL_RUNTIME",
        health=("AUDIT_READ_ONLY_HEALTH", "REPLAY_READ_ONLY_HEALTH"),
    ),
    _definition(
        ControlledActivationCapability.ALERT_DISPATCH,
        "HIGH",
        "CONTROLLED_DISPATCH",
        (ControlledActivationCapability.MONITORING_RUNTIME,),
    ),
    _definition(
        ControlledActivationCapability.EXTERNAL_NOTIFICATION,
        "CRITICAL",
        "EXTERNAL_SIDE_EFFECT",
        (ControlledActivationCapability.ALERT_DISPATCH,),
    ),
)

CAPABILITY_BY_ID = {item.identifier: item for item in CAPABILITY_REGISTRY}
CANONICAL_CAPABILITY_ORDER = tuple(item.identifier for item in CAPABILITY_REGISTRY)
