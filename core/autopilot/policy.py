"""Stable AUTO-01 architecture policy."""

from __future__ import annotations

from dataclasses import dataclass

from .models import AutonomousDeliveryArchitectureDecision


@dataclass(frozen=True, slots=True)
class AutonomousDeliveryPolicy:
    control_plane_owner: str = "AIControlCenter"
    codex_bounded_executor_only: bool = True
    default_least_privilege: bool = True
    production_authorized: bool = False
    ubuntu_stateless_worker_only: bool = True
    persistent_runner_created: bool = False
    decision: AutonomousDeliveryArchitectureDecision = (
        AutonomousDeliveryArchitectureDecision.READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE
    )
