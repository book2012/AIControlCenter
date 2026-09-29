"""Offline Control Plane authorization gate for future provider requests.

The gate evaluates immutable request metadata and opaque capabilities.  It
does not open sockets, resolve credentials, or invoke a provider transport.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.shopping.ports.destination_resolution import DestinationHandle
from core.shopping.ports.phone_verification import ProviderSourceIdentifier
from core.shopping.ports.provider_activation import (
    OpaqueDestinationAllowlist, OperationAllowlist, ProviderActivationError,
    ProviderActivationState, ProviderAllowlist,
    ProviderEnvironment, ProviderOperation,
    ProviderRequestIdentity, READ_OPERATIONS, WRITE_OPERATIONS,
)


class ProviderAuthorizationReason(str, Enum):
    ACTIVATION_DISABLED = "ACTIVATION_DISABLED"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    READ_CAPABILITY_REQUIRED = "READ_CAPABILITY_REQUIRED"
    WRITE_CAPABILITY_REQUIRED = "WRITE_CAPABILITY_REQUIRED"
    PROVIDER_NOT_ALLOWLISTED = "PROVIDER_NOT_ALLOWLISTED"
    OPERATION_NOT_ALLOWLISTED = "OPERATION_NOT_ALLOWLISTED"
    NONPRODUCTION_REQUIRED = "NONPRODUCTION_REQUIRED"
    DESTINATION_REQUIRED = "DESTINATION_REQUIRED"
    DESTINATION_NOT_ALLOWLISTED = "DESTINATION_NOT_ALLOWLISTED"
    INVALID_REQUEST = "INVALID_REQUEST"


CONTROLLED_NONPRODUCTION_ENVIRONMENT = ProviderEnvironment.CONTROLLED_NONPRODUCTION


class ProviderNetworkAuthorizationError(ProviderActivationError):
    """Safe authorization failure; no request or secret details are retained."""


@dataclass(frozen=True, slots=True)
class ProviderNetworkAuthorizationRequest:
    provider_source: ProviderSourceIdentifier
    operation: ProviderOperation
    identity: ProviderRequestIdentity
    environment: ProviderEnvironment = CONTROLLED_NONPRODUCTION_ENVIRONMENT
    destination_handle: DestinationHandle | None = None

    def __post_init__(self) -> None:
        if type(self.provider_source) is str:
            object.__setattr__(self, "provider_source", ProviderSourceIdentifier(value=self.provider_source))
        if type(self.operation) is str:
            object.__setattr__(self, "operation", ProviderOperation(self.operation))
        if isinstance(self.identity, dict):
            object.__setattr__(
                self, "identity", ProviderRequestIdentity.model_validate(self.identity)
            )
        if type(self.provider_source) is not ProviderSourceIdentifier:
            raise TypeError("provider source is invalid")
        if type(self.operation) is not ProviderOperation:
            raise TypeError("provider operation is invalid")
        if type(self.identity) is not ProviderRequestIdentity:
            raise TypeError("request identity is invalid")
        if type(self.environment) is not ProviderEnvironment:
            raise TypeError("request environment is invalid")
        if self.destination_handle is not None and type(self.destination_handle) is not DestinationHandle:
            raise TypeError("destination handle is invalid")

    def __repr__(self) -> str:
        return (
            "ProviderNetworkAuthorizationRequest(provider_source=<bounded>, "
            f"operation={self.operation.value!r}, identity={self.identity!r}, "
            f"environment={self.environment.value!r}, destination_handle=<opaque>)"
        )


@dataclass(frozen=True, slots=True)
class ProviderNetworkAuthorizationDecision:
    allowed: bool
    reason: ProviderAuthorizationReason
    activation_state: ProviderActivationState
    provider_source: ProviderSourceIdentifier
    operation: ProviderOperation
    request_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        if type(self.allowed) is not bool or self.allowed:
            raise ValueError("C5-B authorization decisions are deny-only")

    @property
    def reason_code(self) -> str:
        return self.reason.value

    def to_log_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason_code": self.reason.value,
            "activation_state": self.activation_state.value,
            "provider_source": str(self.provider_source),
            "operation": self.operation.value,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
        }

    def __repr__(self) -> str:
        return (
            "ProviderNetworkAuthorizationDecision("
            f"allowed={self.allowed!r}, reason={self.reason.value!r}, "
            f"activation_state={self.activation_state.value!r})"
        )


class ProviderNetworkAuthorizationGate:
    """Evaluate a future request against explicit Control Plane policy."""

    __slots__ = (
        "activation_state", "provider_allowlist", "read_operation_allowlist",
        "write_operation_allowlist", "destination_allowlist", "_sealed",
    )

    def __init__(
        self,
        *,
        activation_state: ProviderActivationState = ProviderActivationState.DISABLED,
        provider_allowlist: ProviderAllowlist | None = None,
        read_operation_allowlist: OperationAllowlist | None = None,
        write_operation_allowlist: OperationAllowlist | None = None,
        destination_allowlist: OpaqueDestinationAllowlist | None = None,
    ) -> None:
        object.__setattr__(self, "_sealed", False)
        if type(activation_state) is not ProviderActivationState:
            raise TypeError("activation state is invalid")
        object.__setattr__(self, "activation_state", activation_state)
        object.__setattr__(self, "provider_allowlist", provider_allowlist or ProviderAllowlist())
        object.__setattr__(self, "read_operation_allowlist", read_operation_allowlist or OperationAllowlist(
            operations=tuple(sorted(READ_OPERATIONS, key=lambda item: item.value)),
        ))
        object.__setattr__(self, "write_operation_allowlist", write_operation_allowlist or OperationAllowlist(
            operations=tuple(sorted(WRITE_OPERATIONS, key=lambda item: item.value)),
        ))
        object.__setattr__(self, "destination_allowlist", destination_allowlist or OpaqueDestinationAllowlist())
        if type(self.provider_allowlist) is not ProviderAllowlist:
            raise TypeError("provider allowlist is invalid")
        if type(self.read_operation_allowlist) is not OperationAllowlist:
            raise TypeError("read operation allowlist is invalid")
        if type(self.write_operation_allowlist) is not OperationAllowlist:
            raise TypeError("write operation allowlist is invalid")
        if type(self.destination_allowlist) is not OpaqueDestinationAllowlist:
            raise TypeError("destination allowlist is invalid")
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("authorization gates are immutable")
        object.__setattr__(self, name, value)

    @staticmethod
    def _decision(request: ProviderNetworkAuthorizationRequest, state: ProviderActivationState,
                  reason: ProviderAuthorizationReason, allowed: bool) -> ProviderNetworkAuthorizationDecision:
        return ProviderNetworkAuthorizationDecision(
            # C5-B is an offline deny-only foundation.  No caller-controlled
            # value can change the outcome of this helper.
            allowed=False, reason=reason, activation_state=state,
            provider_source=request.provider_source, operation=request.operation,
            request_id=request.identity.request_id, correlation_id=request.identity.correlation_id,
        )

    def authorize(
        self,
        request: ProviderNetworkAuthorizationRequest,
        *,
        capability: object | None = None,
    ) -> ProviderNetworkAuthorizationDecision:
        if type(request) is not ProviderNetworkAuthorizationRequest:
            raise ProviderNetworkAuthorizationError(ProviderAuthorizationReason.INVALID_REQUEST.value)
        if self.activation_state is ProviderActivationState.DISABLED:
            return self._decision(request, self.activation_state,
                                  ProviderAuthorizationReason.ACTIVATION_DISABLED, False)
        if self.activation_state is ProviderActivationState.CONTRACT_ONLY:
            return self._decision(request, self.activation_state,
                                  ProviderAuthorizationReason.CONTRACT_ONLY, False)
        if not self.provider_allowlist.contains(request.provider_source):
            return self._decision(request, self.activation_state,
                                  ProviderAuthorizationReason.PROVIDER_NOT_ALLOWLISTED, False)
        if request.operation in READ_OPERATIONS:
            if self.activation_state is not ProviderActivationState.AUTHENTICATED_READ_ONLY:
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.WRITE_CAPABILITY_REQUIRED, False)
            if not self.read_operation_allowlist.contains(request.operation):
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.OPERATION_NOT_ALLOWLISTED, False)
            return self._decision(request, self.activation_state,
                                  ProviderAuthorizationReason.READ_CAPABILITY_REQUIRED, False)
        if request.operation in WRITE_OPERATIONS:
            if self.activation_state is not ProviderActivationState.CONTROLLED_NONPROD_WRITE:
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.WRITE_CAPABILITY_REQUIRED, False)
            if request.environment is not CONTROLLED_NONPRODUCTION_ENVIRONMENT:
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.NONPRODUCTION_REQUIRED, False)
            if not self.write_operation_allowlist.contains(request.operation):
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.OPERATION_NOT_ALLOWLISTED, False)
            if request.destination_handle is None:
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.DESTINATION_REQUIRED, False)
            if not self.destination_allowlist.contains(request.destination_handle):
                return self._decision(request, self.activation_state,
                                      ProviderAuthorizationReason.DESTINATION_NOT_ALLOWLISTED, False)
            return self._decision(request, self.activation_state,
                                  ProviderAuthorizationReason.WRITE_CAPABILITY_REQUIRED, False)
        return self._decision(request, self.activation_state,
                              ProviderAuthorizationReason.OPERATION_NOT_ALLOWLISTED, False)

    def require(
        self,
        request: ProviderNetworkAuthorizationRequest,
        *,
        capability: object | None = None,
    ) -> ProviderNetworkAuthorizationDecision:
        decision = self.authorize(request, capability=capability)
        if not decision.allowed:
            raise ProviderNetworkAuthorizationError(decision.reason.value)
        return decision

    @property
    def max_attempts(self) -> int:
        return 1

    @property
    def automatic_retry_enabled(self) -> bool:
        return False

    @property
    def fallback_provider_enabled(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"ProviderNetworkAuthorizationGate(state={self.activation_state.value!r})"


ProviderNetworkAuthorization = ProviderNetworkAuthorizationGate
NetworkAuthorizationGate = ProviderNetworkAuthorizationGate


__all__ = [
    "NetworkAuthorizationGate",
    "CONTROLLED_NONPRODUCTION_ENVIRONMENT", "ProviderAuthorizationReason",
    "ProviderNetworkAuthorization",
    "ProviderNetworkAuthorizationDecision", "ProviderNetworkAuthorizationError",
    "ProviderNetworkAuthorizationGate", "ProviderNetworkAuthorizationRequest",
]
