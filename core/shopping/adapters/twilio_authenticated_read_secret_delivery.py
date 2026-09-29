from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from core.secrets.ports import (
    EphemeralSecretLease,
    SecretReference,
    SecretResolverPort,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadCapability,
    TwilioAuthenticatedReadDecision,
)
from core.shopping.ports.provider_activation import (
    AuthenticatedReadCapability,
    SecretDeliveryContract,
)
from core.shopping.ports.provider_authenticated_read import (
    AuthenticatedProviderReadPort,
)


TWILIO_SECRET_BACKEND = "macos.keychain"


class TwilioSecretDeliveryReason(str, Enum):
    INVALID_REFERENCE = "INVALID_REFERENCE"
    BACKEND_REJECTED = "BACKEND_REJECTED"
    DUPLICATE_REFERENCE = "DUPLICATE_REFERENCE"
    OFFLINE_TRANSPORT_DISABLED = "OFFLINE_TRANSPORT_DISABLED"


class TwilioSecretDeliveryError(RuntimeError):
    """Bounded C5-C3B failure with no secret material."""

    def __init__(
        self,
        reason: TwilioSecretDeliveryReason,
    ) -> None:
        if type(reason) is not TwilioSecretDeliveryReason:
            reason = TwilioSecretDeliveryReason.INVALID_REFERENCE

        self.reason = reason
        super().__init__(reason.value)

    @property
    def reason_code(self) -> str:
        return self.reason.value

    def __repr__(self) -> str:
        return (
            "TwilioSecretDeliveryError("
            f"reason_code={self.reason.value!r})"
        )


@dataclass(frozen=True, slots=True)
class TwilioCredentialReferences:
    """Value-free references for future Twilio Basic authentication."""

    api_key_sid_reference: SecretReference
    api_key_secret_reference: SecretReference

    def __post_init__(self) -> None:
        for reference in (
            self.api_key_sid_reference,
            self.api_key_secret_reference,
        ):
            if type(reference) is not SecretReference:
                raise TwilioSecretDeliveryError(
                    TwilioSecretDeliveryReason.INVALID_REFERENCE
                )

            if reference.backend != TWILIO_SECRET_BACKEND:
                raise TwilioSecretDeliveryError(
                    TwilioSecretDeliveryReason.BACKEND_REJECTED
                )

        if (
            self.api_key_sid_reference.backend
            == self.api_key_secret_reference.backend
            and self.api_key_sid_reference.key_name
            == self.api_key_secret_reference.key_name
        ):
            raise TwilioSecretDeliveryError(
                TwilioSecretDeliveryReason.DUPLICATE_REFERENCE
            )

    @property
    def delivery_contracts(
        self,
    ) -> tuple[
        SecretDeliveryContract,
        SecretDeliveryContract,
    ]:
        return (
            SecretDeliveryContract(
                reference=self.api_key_sid_reference,
            ),
            SecretDeliveryContract(
                reference=self.api_key_secret_reference,
            ),
        )

    def __repr__(self) -> str:
        return (
            "TwilioCredentialReferences("
            "<metadata-only, values-redacted>)"
        )


@dataclass(frozen=True, slots=True)
class TwilioSecretDeliveryPlan:
    """Authorization-approved metadata plan; contains no secret value."""

    credentials: TwilioCredentialReferences
    authorization: TwilioAuthenticatedReadDecision

    def __post_init__(self) -> None:
        if type(self.credentials) is not TwilioCredentialReferences:
            raise TypeError("Twilio credential references are required")

        if type(self.authorization) is not TwilioAuthenticatedReadDecision:
            raise TypeError("Twilio authorization decision is required")

        if not self.authorization.allowed:
            raise ValueError(
                "secret delivery plan requires authorized read"
            )

    @property
    def delivery_contracts(
        self,
    ) -> tuple[
        SecretDeliveryContract,
        SecretDeliveryContract,
    ]:
        return self.credentials.delivery_contracts

    @property
    def resolver_contract(self) -> str:
        return "SecretResolverPort"

    @property
    def lease_contract(self) -> str:
        return "EphemeralSecretLease"

    @property
    def consumer_boundary(self) -> str:
        return "TWILIO_AUTHENTICATED_READ_TRANSPORT_ONLY"

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def credential_resolution_performed(self) -> bool:
        return False

    @property
    def transport_constructed(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "TwilioSecretDeliveryPlan("
            "authorized=True, credentials=<metadata-only>, "
            "network_enabled=False)"
        )


@dataclass(frozen=True, slots=True)
class TwilioSecretDeliveryPreparation:
    """Result of authorization-first offline preparation."""

    authorization: TwilioAuthenticatedReadDecision
    plan: TwilioSecretDeliveryPlan | None

    def __post_init__(self) -> None:
        if type(self.authorization) is not TwilioAuthenticatedReadDecision:
            raise TypeError("Twilio authorization decision is required")

        if self.authorization.allowed:
            if type(self.plan) is not TwilioSecretDeliveryPlan:
                raise ValueError(
                    "authorized preparation requires delivery plan"
                )
        elif self.plan is not None:
            raise ValueError(
                "denied preparation cannot contain delivery plan"
            )

    @property
    def prepared(self) -> bool:
        return self.authorization.allowed and self.plan is not None

    def __repr__(self) -> str:
        return (
            "TwilioSecretDeliveryPreparation("
            f"prepared={self.prepared!r}, "
            "secret_material=<absent>)"
        )


@runtime_checkable
class TwilioLeaseTransportBuilder(Protocol):
    """Future C5-C3C transport builder consuming only ephemeral leases."""

    def build_authenticated_read_transport(
        self,
        *,
        api_key_sid_lease: EphemeralSecretLease,
        api_key_secret_lease: EphemeralSecretLease,
        capability: AuthenticatedReadCapability,
    ) -> AuthenticatedProviderReadPort:
        ...


class TwilioOfflineAuthenticatedReadTransportFactory:
    """C5-C3B deny-only factory.

    It validates the future outer seam but deliberately never resolves a
    SecretReference, consumes an EphemeralSecretLease, or constructs a
    provider transport.
    """

    __slots__ = ()

    def create_authenticated_read_transport(
        self,
        *,
        credentials: TwilioCredentialReferences,
        secret_resolver: SecretResolverPort,
        capability: TwilioAuthenticatedReadCapability,
    ) -> AuthenticatedProviderReadPort:
        if type(credentials) is not TwilioCredentialReferences:
            raise TypeError("Twilio credential references are required")

        if not isinstance(secret_resolver, SecretResolverPort):
            raise TypeError("secret resolver port is required")

        if type(capability) is not TwilioAuthenticatedReadCapability:
            raise TypeError(
                "Twilio authenticated read capability is required"
            )

        raise TwilioSecretDeliveryError(
            TwilioSecretDeliveryReason.OFFLINE_TRANSPORT_DISABLED
        )

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def credential_resolution_performed(self) -> bool:
        return False

    @property
    def transport_constructed(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "TwilioOfflineAuthenticatedReadTransportFactory("
            "network_enabled=False, "
            "credential_resolution_performed=False)"
        )
