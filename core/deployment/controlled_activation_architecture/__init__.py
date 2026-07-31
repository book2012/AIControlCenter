"""M4-A1 pure controlled activation architecture boundary."""

from .models import (
    BASELINE_COMMIT,
    BRANCH,
    M3_READINESS,
    ControlledActivationArchitectureConfig,
    ControlledActivationArchitectureDecision,
    ControlledActivationArchitectureError,
    ControlledActivationArchitecturePolicy,
    ControlledActivationCapability,
    ControlledActivationCapabilityDefinition,
    ControlledActivationPlan,
    ControlledActivationPlanRequest,
    ControlledActivationPlanStep,
    ControlledActivationState,
    ControlledActivationTransition,
    ControlledActivationValidationResult,
)
from .planner import ControlledActivationPlanner
from .architecture_policy import validate_architecture_config, validate_plan_request
from .registry import (
    CANONICAL_CAPABILITY_ORDER,
    CAPABILITY_BY_ID,
    CAPABILITY_REGISTRY,
)
from .state_machine import ControlledActivationStateMachine
from .validation import ControlledActivationArchitectureValidationService

__all__ = (
    "BASELINE_COMMIT",
    "BRANCH",
    "M3_READINESS",
    "CANONICAL_CAPABILITY_ORDER",
    "CAPABILITY_BY_ID",
    "CAPABILITY_REGISTRY",
    "ControlledActivationArchitectureConfig",
    "ControlledActivationArchitectureDecision",
    "ControlledActivationArchitectureError",
    "ControlledActivationArchitecturePolicy",
    "ControlledActivationArchitectureValidationService",
    "ControlledActivationCapability",
    "ControlledActivationCapabilityDefinition",
    "ControlledActivationPlan",
    "ControlledActivationPlanner",
    "ControlledActivationPlanRequest",
    "ControlledActivationPlanStep",
    "ControlledActivationState",
    "ControlledActivationStateMachine",
    "ControlledActivationTransition",
    "ControlledActivationValidationResult",
    "validate_architecture_config",
    "validate_plan_request",
)
