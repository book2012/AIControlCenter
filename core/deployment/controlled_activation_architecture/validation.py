"""Facade validating architecture configuration before deterministic planning."""

from __future__ import annotations

from .models import (
    ControlledActivationArchitectureConfig,
    ControlledActivationPlan,
    ControlledActivationPlanRequest,
)
from .planner import ControlledActivationPlanner
from .architecture_policy import validate_architecture_config


class ControlledActivationArchitectureValidationService:
    def __init__(self) -> None:
        self._planner = ControlledActivationPlanner()

    def validate_and_plan(
        self,
        config: ControlledActivationArchitectureConfig,
        request: ControlledActivationPlanRequest,
    ) -> ControlledActivationPlan:
        validate_architecture_config(config)
        return self._planner.plan(request)
