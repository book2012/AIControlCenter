from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
)
from core.shopping.ports.provider_activation import (
    ProviderActivationState,
)


@dataclass(frozen=True, slots=True)
class TwilioAuthenticatedReadAuthorizationComposition:
    """Offline C5-C3A authorization composition owned by AIControlCenter."""

    authority: TwilioAuthenticatedReadAuthority
    activation_state: ProviderActivationState = (
        ProviderActivationState.CONTRACT_ONLY
    )

    def __post_init__(self) -> None:
        if type(self.authority) is not TwilioAuthenticatedReadAuthority:
            raise TypeError(
                "Twilio authenticated-read authority is required"
            )

        if (
            self.activation_state
            is not ProviderActivationState.CONTRACT_ONLY
        ):
            raise ValueError(
                "C5-C3A composition must remain CONTRACT_ONLY"
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

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadAuthorizationComposition("
            "activation_state='CONTRACT_ONLY', "
            "generic_authorization_model='OFFLINE_DENY_ONLY', "
            "network_enabled=False)"
        )


def build_twilio_authenticated_read_authorization(
    *,
    clock: Callable[[], datetime] | None = None,
    id_factory: Callable[[], str] | None = None,
) -> TwilioAuthenticatedReadAuthorizationComposition:
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=id_factory,
    )

    return TwilioAuthenticatedReadAuthorizationComposition(
        authority=authority,
    )
