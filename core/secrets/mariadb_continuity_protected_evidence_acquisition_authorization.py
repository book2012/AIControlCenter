"""One-shot, acquisition-specific authorization values with zero execution authority."""

from dataclasses import dataclass
from enum import Enum
from threading import Lock

from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING,
    ProtectedExternalEvidenceConcreteSourceLocationIdentity,
)
from core.secrets.mariadb_continuity_evidence_fixed_source_slot import (
    ProtectedExternalEvidenceFixedSourceSlotIdentity,
)
from core.secrets.mariadb_continuity_protected_evidence_leaf_locator import (
    ConcreteProtectedEvidenceLeafPath,
    LOCATION_TO_EXACT_LEAF_BASENAME,
)


class AcquisitionAuthorizationError(ValueError):
    pass


class AcquisitionAuthorizationConsumptionState(str, Enum):
    COMMITTED = "COMMITTED"


class ProtectedEvidenceAcquisitionInvocationCapabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    CONSUMED = "CONSUMED"


@dataclass(frozen=True, slots=True, init=False)
class ProtectedEvidenceAcquisitionRequest:
    acquisition_request_id: str
    fixed_source_slot_identity: ProtectedExternalEvidenceFixedSourceSlotIdentity
    concrete_source_location_identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity
    leaf_basename: str
    concrete_parent_path: str
    concrete_leaf_path: str
    _repository_composed_concrete_leaf_path: str

    def __new__(cls):
        raise TypeError("request is issued only by the repository boundary")


def _validate_request_binding(request: ProtectedEvidenceAcquisitionRequest) -> None:
        if type(request.acquisition_request_id) is not str or not request.acquisition_request_id:
            raise AcquisitionAuthorizationError("acquisition_request_id must be non-empty text")
        if type(request.fixed_source_slot_identity) is not ProtectedExternalEvidenceFixedSourceSlotIdentity:
            raise AcquisitionAuthorizationError("fixed source slot identity is invalid")
        if type(request.concrete_source_location_identity) is not ProtectedExternalEvidenceConcreteSourceLocationIdentity:
            raise AcquisitionAuthorizationError("concrete source location identity is invalid")
        expected_location = FIXED_SOURCE_SLOT_TO_CONCRETE_LOCATION_MAPPING[request.fixed_source_slot_identity]
        if request.concrete_source_location_identity is not expected_location:
            raise AcquisitionAuthorizationError("slot and location are not repository-bound")
        expected_basename = LOCATION_TO_EXACT_LEAF_BASENAME[expected_location]
        if type(request.leaf_basename) is not str or request.leaf_basename != expected_basename:
            raise AcquisitionAuthorizationError("leaf basename is not repository-bound")
        expected_leaf_path = request.concrete_parent_path + "/" + expected_basename
        if (type(request.concrete_parent_path) is not str
                or type(request.concrete_leaf_path) is not str
                or request.concrete_leaf_path != expected_leaf_path
                or request._repository_composed_concrete_leaf_path != expected_leaf_path):
            raise AcquisitionAuthorizationError("parent and leaf path are not exactly repository-bound")


def acquisition_request(
    acquisition_request_id: str, leaf: ConcreteProtectedEvidenceLeafPath
) -> ProtectedEvidenceAcquisitionRequest:
    if type(leaf) is not ConcreteProtectedEvidenceLeafPath:
        raise TypeError("leaf must be exactly ConcreteProtectedEvidenceLeafPath")
    if type(acquisition_request_id) is not str or not acquisition_request_id:
        raise AcquisitionAuthorizationError("acquisition_request_id must be non-empty text")
    value = object.__new__(ProtectedEvidenceAcquisitionRequest)
    object.__setattr__(value, "acquisition_request_id", acquisition_request_id)
    object.__setattr__(value, "fixed_source_slot_identity", leaf.fixed_source_slot_identity)
    object.__setattr__(value, "concrete_source_location_identity", leaf.concrete_source_location_identity)
    object.__setattr__(value, "leaf_basename", leaf.leaf_basename)
    object.__setattr__(value, "concrete_parent_path", leaf.concrete_parent_path)
    object.__setattr__(value, "concrete_leaf_path", leaf.concrete_leaf_path)
    object.__setattr__(value, "_repository_composed_concrete_leaf_path", leaf.concrete_leaf_path)
    _validate_request_binding(value)
    return value


@dataclass(frozen=True, slots=True, init=False)
class ProtectedEvidenceAcquisitionAuthorization:
    """Repository binding only; an identifier is not human authorization evidence."""
    authorization_id: str
    acquisition_request_id: str
    fixed_source_slot_identity: ProtectedExternalEvidenceFixedSourceSlotIdentity
    concrete_source_location_identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity
    leaf_basename: str
    concrete_parent_path: str
    concrete_leaf_path: str
    maximum_acquisition_attempts: int
    human_authorization_evidence_supplied: bool
    authorization_authority: bool

    def __new__(cls):
        raise TypeError("authorization is issued only by the repository boundary")


@dataclass(frozen=True, slots=True, init=False, repr=False)
class ProtectedEvidenceHumanAuthorizationEvidence:
    """Factual DTO only. This repository intentionally provides no trusted issuer."""

    authorization_id: str
    acquisition_request_id: str

    def __new__(cls):
        raise TypeError("human authorization evidence requires a separate trusted issuer")

    def __repr__(self) -> str:
        return "ProtectedEvidenceHumanAuthorizationEvidence(<opaque>)"

    def __copy__(self):
        raise TypeError("human authorization evidence cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("human authorization evidence cannot be deep-copied")

    def __reduce__(self):
        raise TypeError("human authorization evidence cannot be serialized")

    def __hash__(self):
        raise TypeError("human authorization evidence cannot be hashed")


def issue_acquisition_authorization(
    authorization_id: str, request: ProtectedEvidenceAcquisitionRequest
) -> ProtectedEvidenceAcquisitionAuthorization:
    if type(authorization_id) is not str or not authorization_id:
        raise AcquisitionAuthorizationError("authorization_id must be non-empty text")
    validate_acquisition_request(request)
    value = object.__new__(ProtectedEvidenceAcquisitionAuthorization)
    for name in (
        "acquisition_request_id", "fixed_source_slot_identity",
        "concrete_source_location_identity", "leaf_basename", "concrete_parent_path", "concrete_leaf_path",
    ):
        object.__setattr__(value, name, getattr(request, name))
    object.__setattr__(value, "authorization_id", authorization_id)
    object.__setattr__(value, "maximum_acquisition_attempts", 1)
    object.__setattr__(value, "human_authorization_evidence_supplied", False)
    object.__setattr__(value, "authorization_authority", False)
    return value


def validate_acquisition_request(request: ProtectedEvidenceAcquisitionRequest) -> None:
    if type(request) is not ProtectedEvidenceAcquisitionRequest:
        raise AcquisitionAuthorizationError("request has not been repository-issued")
    # Re-run all bindings so object.__setattr__ tampering cannot cross the boundary.
    _validate_request_binding(request)


@dataclass(frozen=True, slots=True, init=False)
class ProtectedEvidenceAcquisitionConsumptionReceipt:
    authorization_id: str
    acquisition_request_id: str
    fixed_source_slot_identity: ProtectedExternalEvidenceFixedSourceSlotIdentity
    concrete_source_location_identity: ProtectedExternalEvidenceConcreteSourceLocationIdentity
    leaf_basename: str
    concrete_parent_path: str
    concrete_leaf_path: str
    maximum_acquisition_attempts: int
    state: AcquisitionAuthorizationConsumptionState
    binding_digest: str
    committed_digest: str

    def __new__(cls):
        raise TypeError("receipt is emitted only by durable consumption")


@dataclass(frozen=True, slots=True, init=False)
class ProtectedEvidenceAcquisitionAuthorizationConsumptionResult:
    receipt: ProtectedEvidenceAcquisitionConsumptionReceipt

    def __new__(cls):
        raise TypeError("result is emitted only by durable consumption")


class RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption(RuntimeError):
    pass


@dataclass(frozen=True, slots=True, init=False, repr=False)
class ProtectedEvidenceHumanAuthorizationValidation:
    """Separate validation contract; no Production issuer exists in this milestone."""

    authorization_id: str
    acquisition_request_id: str
    production_authority: bool

    def __new__(cls):
        raise TypeError("human authorization validation requires a separate trusted issuer")

    def __repr__(self) -> str:
        return "ProtectedEvidenceHumanAuthorizationValidation(<opaque>)"


@dataclass(frozen=True, slots=True, init=False, repr=False)
class ProtectedEvidenceAcquisitionInvocationCapability:
    """Opaque process-local authority for exactly one acquisition invocation."""

    _request: ProtectedEvidenceAcquisitionRequest
    _state: ProtectedEvidenceAcquisitionInvocationCapabilityState
    _lock: Lock

    def __new__(cls):
        raise TypeError("invocation capability requires a future trusted composition boundary")

    def __repr__(self) -> str:
        return "ProtectedEvidenceAcquisitionInvocationCapability(<opaque>)"

    def __copy__(self):
        raise TypeError("invocation capability cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("invocation capability cannot be deep-copied")

    def __reduce__(self):
        raise TypeError("invocation capability cannot be serialized")

    def __hash__(self):
        raise TypeError("invocation capability cannot be hashed")


def _consume_invocation_capability(capability, request):
    if type(capability) is not ProtectedEvidenceAcquisitionInvocationCapability:
        raise AcquisitionAuthorizationError("exact invocation capability is required")
    if type(capability._lock) is not type(Lock()):
        raise AcquisitionAuthorizationError("capability lock is invalid")
    with capability._lock:
        if capability._state is not ProtectedEvidenceAcquisitionInvocationCapabilityState.AVAILABLE:
            raise RepeatedProtectedEvidenceAcquisitionAuthorizationConsumption("invocation capability is consumed")
        binding_names = ("acquisition_request_id", "fixed_source_slot_identity",
                         "concrete_source_location_identity", "leaf_basename",
                         "concrete_parent_path", "concrete_leaf_path")
        if any(getattr(capability._request, name) != getattr(request, name)
               for name in binding_names):
            raise AcquisitionAuthorizationError("capability is not bound to this request")
        object.__setattr__(capability, "_state", ProtectedEvidenceAcquisitionInvocationCapabilityState.CONSUMED)


__all__ = tuple(name for name in globals() if name.startswith("Protected") or name.startswith("Acquisition") or name.startswith("Repeated")) + (
    "acquisition_request", "issue_acquisition_authorization", "validate_acquisition_request",
)
