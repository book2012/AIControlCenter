from __future__ import annotations

from dataclasses import dataclass

from core.secrets.ports import SecretReference
from core.shopping.adapters.twilio_authenticated_read_secret_delivery import (
    TwilioCredentialReferences,
    TwilioOfflineAuthenticatedReadTransportFactory,
    TwilioSecretDeliveryPlan,
    TwilioSecretDeliveryPreparation,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import (
    ProviderActivationState,
)


@dataclass(frozen=True, slots=True)
class TwilioAuthenticatedReadSecretComposition:
    """C5-C3B offline, authorization-first Mac composition."""

    authority: TwilioAuthenticatedReadAuthority
    credentials: TwilioCredentialReferences
    transport_factory: TwilioOfflineAuthenticatedReadTransportFactory
    activation_state: ProviderActivationState = (
        ProviderActivationState.CONTRACT_ONLY
    )

    def __post_init__(self) -> None:
        if type(self.authority) is not TwilioAuthenticatedReadAuthority:
            raise TypeError(
                "Twilio authenticated read authority is required"
            )

        if type(self.credentials) is not TwilioCredentialReferences:
            raise TypeError(
                "Twilio credential references are required"
            )

        if (
            type(self.transport_factory)
            is not TwilioOfflineAuthenticatedReadTransportFactory
        ):
            raise TypeError(
                "offline Twilio transport factory is required"
            )

        if (
            self.activation_state
            is not ProviderActivationState.CONTRACT_ONLY
        ):
            raise ValueError(
                "C5-C3B composition must remain CONTRACT_ONLY"
            )

    def prepare(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        capability: object | None,
    ) -> TwilioSecretDeliveryPreparation:
        if type(request) is not TwilioAuthenticatedReadRequest:
            raise TypeError(
                "Twilio authenticated read request is required"
            )

        authorization = self.authority.authorize_once(
            request,
            capability=capability,
        )

        if not authorization.allowed:
            return TwilioSecretDeliveryPreparation(
                authorization=authorization,
                plan=None,
            )

        plan = TwilioSecretDeliveryPlan(
            credentials=self.credentials,
            authorization=authorization,
        )

        return TwilioSecretDeliveryPreparation(
            authorization=authorization,
            plan=plan,
        )

    @property
    def generic_authorization_model(self) -> str:
        return "OFFLINE_DENY_ONLY"

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def credential_resolution_performed(self) -> bool:
        return False

    @property
    def keychain_accessed(self) -> bool:
        return False

    @property
    def transport_constructed(self) -> bool:
        return False

    @property
    def provider_transport(self) -> None:
        return None

    @property
    def secret_resolver(self) -> None:
        return None

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadSecretComposition("
            "activation_state='CONTRACT_ONLY', "
            "network_enabled=False, "
            "credential_resolution_performed=False)"
        )


def build_twilio_authenticated_read_secret_composition(
    *,
    authority: TwilioAuthenticatedReadAuthority,
    api_key_sid_reference: SecretReference,
    api_key_secret_reference: SecretReference,
) -> TwilioAuthenticatedReadSecretComposition:
    if type(authority) is not TwilioAuthenticatedReadAuthority:
        raise TypeError(
            "Twilio authenticated read authority is required"
        )

    credentials = TwilioCredentialReferences(
        api_key_sid_reference=api_key_sid_reference,
        api_key_secret_reference=api_key_secret_reference,
    )

    return TwilioAuthenticatedReadSecretComposition(
        authority=authority,
        credentials=credentials,
        transport_factory=(
            TwilioOfflineAuthenticatedReadTransportFactory()
        ),
    )
