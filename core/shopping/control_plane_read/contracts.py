"""Synthetic future operation descriptions, never authorization or operators."""
from dataclasses import dataclass
from enum import Enum
from .capability import ShoppingReadVerifier, CapabilityError

WORK_ITEM = "SHOP-SERVICE-START-01E"
MUTATION_ID = "shopping-read-verifier-v1-cas"
PLUGIN = "ai-controlcenter-shopping-read"
OPTION = "aicontrolcenter_shopping_read_verifier_v1"
CONTEXT = "colima-aicontrolcenter-commerce"
PROJECT = "ai-shopping"
CONTAINER = "shopping-wordpress"
PUBLIC_EDGE_DENY_PREFIX = "/wp-json/aicontrolcenter/v1/shopping/"
MAXIMUM_USES = 1
AUTOMATIC_RETRY = False
OPTION_AUTOLOAD = False
LIVE_OPERATOR_AVAILABLE = False
PUBLIC_EDGE_RUNTIME_ISOLATION_PROVEN = False
DEPLOYMENT_LOGGING_SAFETY_PROVEN = False


@dataclass(frozen=True, slots=True)
class VerifierCASContract:
    expected: ShoppingReadVerifier | None
    pending: ShoppingReadVerifier

    def __post_init__(self):
        if type(self.pending) is not ShoppingReadVerifier or (self.expected is not None and type(self.expected) is not ShoppingReadVerifier):
            raise CapabilityError()

    def boundary_payload(self):
        """Explicit verifier-only boundary. Never send to logs or ordinary results."""
        return {"work_item": WORK_ITEM, "mutation_id": MUTATION_ID,
                "plugin": PLUGIN, "option": OPTION, "context": CONTEXT,
                "project": PROJECT, "container": CONTAINER, "maximum_uses": 1,
                "automatic_retry": False, "autoload": False,
                "expected_verifier": None if self.expected is None else self.expected._provisioning_digest(),
                "pending_verifier": self.pending._provisioning_digest()}


class RotationState(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    PROMOTED = "PROMOTED"
    FAILED_OR_UNCERTAIN = "FAILED_OR_UNCERTAIN"


@dataclass(frozen=True, slots=True)
class SyntheticRotation:
    state: RotationState = RotationState.ACTIVE
    pending_persisted: bool = False
    old_retired: bool = False

    def advance(self, event):
        """Evidence model only; no file write, CAS, auth issuance or HTTP invocation."""
        transitions = {
            (RotationState.ACTIVE, "pending_generated_locally"): (RotationState.PENDING, False, False),
            (RotationState.PENDING, "pending_persisted_locally"): (RotationState.PENDING, True, False),
            (RotationState.PENDING, "separately_authorized_verifier_cas_confirmed"): (RotationState.VALIDATING, True, False),
            (RotationState.VALIDATING, "pending_authenticated_and_locally_promoted"): (RotationState.PROMOTED, True, False),
            (RotationState.PROMOTED, "old_local_capability_retired"): (RotationState.PROMOTED, True, True),
        }
        if event == "failed_or_uncertain" and self.state != RotationState.FAILED_OR_UNCERTAIN:
            return SyntheticRotation(RotationState.FAILED_OR_UNCERTAIN, self.pending_persisted, self.old_retired)
        if (self.state, event) not in transitions or self.old_retired:
            raise CapabilityError()
        if event == "separately_authorized_verifier_cas_confirmed" and not self.pending_persisted:
            raise CapabilityError()
        if event == "pending_persisted_locally" and self.pending_persisted:
            raise CapabilityError()
        return SyntheticRotation(*transitions[(self.state, event)])
