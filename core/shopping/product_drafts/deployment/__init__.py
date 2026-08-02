"""SHOP-03A controlled fake Commerce write architecture."""
from .authorization import (AuthorizationDecisionValue,
                            CommerceWriteAuthorizationPort,
                            StaticWriteAuthorizationAdapter,
                            WriteAuthorizationDecision)
from .eligibility import EligibilityResult, RejectionReason, evaluate_eligibility
from .fake_adapter import FakeCallSummary, FakeCommerceProductWriteAdapter
from .idempotency import IdempotencyConflict, InMemoryWriteIdempotencyStore
from .models import (CommerceOperation, ControlledDeploymentIntent,
                     ControlledWritePlan, SourceFreshnessPolicy, WriteMode)
from .results import ControlledWriteServiceResult, DeploymentOutcome
from .serialization import preview_projection
from .service import ControlledCommerceWriteService
from .write_port import CommerceProductWritePort, CommerceWriteResult

__all__ = [name for name in globals() if not name.startswith("_")]
