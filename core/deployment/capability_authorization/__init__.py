"""M4-A2 capability authorization contract surface."""

from .models import (
    BASELINE_COMMIT,
    BRANCH,
    M3_READINESS,
    M4_A1_DECISION,
    SCHEMA_VERSION,
    CapabilityAuthorizationApproval,
    CapabilityAuthorizationArchitectureDecision,
    CapabilityAuthorizationDecision,
    CapabilityAuthorizationError,
    CapabilityAuthorizationEvidence,
    CapabilityAuthorizationGrant,
    CapabilityAuthorizationPlan,
    CapabilityAuthorizationRequest,
    CapabilityAuthorizationRestriction,
    CapabilityAuthorizationScope,
    CapabilityAuthorizationValidationResult,
)
from .planner import CapabilityAuthorizationPlanner
from .capability_policy import (
    CAPABILITY_REQUIRED_RESTRICTIONS,
    DEPENDENCY_CAPABILITY,
    MAXIMUM_AUTHORIZATION_TTL,
    REQUIRED_RESTRICTIONS,
)
from .validation import validate_approval, validate_request

__all__ = (
    "BASELINE_COMMIT",
    "BRANCH",
    "CAPABILITY_REQUIRED_RESTRICTIONS",
    "DEPENDENCY_CAPABILITY",
    "M3_READINESS",
    "M4_A1_DECISION",
    "MAXIMUM_AUTHORIZATION_TTL",
    "REQUIRED_RESTRICTIONS",
    "SCHEMA_VERSION",
    "CapabilityAuthorizationApproval",
    "CapabilityAuthorizationArchitectureDecision",
    "CapabilityAuthorizationDecision",
    "CapabilityAuthorizationError",
    "CapabilityAuthorizationEvidence",
    "CapabilityAuthorizationGrant",
    "CapabilityAuthorizationPlan",
    "CapabilityAuthorizationPlanner",
    "CapabilityAuthorizationRequest",
    "CapabilityAuthorizationRestriction",
    "CapabilityAuthorizationScope",
    "CapabilityAuthorizationValidationResult",
    "validate_approval",
    "validate_request",
)
