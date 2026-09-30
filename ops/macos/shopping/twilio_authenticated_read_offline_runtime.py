from __future__ import annotations

from dataclasses import dataclass

from core.secrets.ports import (
    SecretReference,
    SecretResolverPort,
)
from core.shopping.adapters.twilio_authenticated_read_offline_transport import (
    TwilioOfflineAuthenticatedReadTransport,
    TwilioOfflineHttpGetExecutor,
    TwilioOfflineObservationNormalizer,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import (
    ProviderActivationState,
)
from core.shopping.ports.provider_authenticated_read import (
    ProviderReadResult,
)
from ops.macos.shopping.twilio_authenticated_read_secret_composition import (
    TwilioAuthenticatedReadSecretComposition,
    build_twilio_authenticated_read_secret_composition,
)


@dataclass(frozen=True)
class TwilioAuthenticatedReadOfflineRuntime:
    """
    Mac-only C5-C3C0 offline simulation composition.

    AUTHENTICATED_READ_ONLY is a future target state only.
    This runtime itself remains CONTRACT_ONLY.
    """

    secret_composition: TwilioAuthenticatedReadSecretComposition
    transport: TwilioOfflineAuthenticatedReadTransport
    activation_state: ProviderActivationState = (
        ProviderActivationState.CONTRACT_ONLY
    )

    def __post_init__(self) -> None:
        if (
            type(self.secret_composition)
            is not TwilioAuthenticatedReadSecretComposition
        ):
            raise TypeError(
                "Twilio secret composition is required"
            )
        if (
            type(self.transport)
            is not TwilioOfflineAuthenticatedReadTransport
        ):
            raise TypeError(
                "offline Twilio transport is required"
            )
        if (
            self.activation_state
            is not ProviderActivationState.CONTRACT_ONLY
        ):
            raise ValueError(
                "C5-C3C0 must remain CONTRACT_ONLY"
            )

    def execute(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        capability: object | None,
    ) -> ProviderReadResult:
        return self.transport.execute(
            request,
            capability=capability,
        )

    @property
    def target_activation_state(
        self,
    ) -> ProviderActivationState:
        return ProviderActivationState.AUTHENTICATED_READ_ONLY

    @property
    def generic_authorization_model(self) -> str:
        return "OFFLINE_DENY_ONLY"

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def real_credential_resolution_enabled(self) -> bool:
        return False

    @property
    def keychain_accessed(self) -> bool:
        return False

    @property
    def sms_enabled(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadOfflineRuntime("
            "activation_state='CONTRACT_ONLY', "
            "target='AUTHENTICATED_READ_ONLY', "
            "network_enabled=False)"
        )


def build_twilio_authenticated_read_offline_runtime(
    *,
    authority: TwilioAuthenticatedReadAuthority,
    api_key_sid_reference: SecretReference,
    api_key_secret_reference: SecretReference,
    secret_resolver: SecretResolverPort,
    executor: TwilioOfflineHttpGetExecutor,
    normalizer: TwilioOfflineObservationNormalizer,
) -> TwilioAuthenticatedReadOfflineRuntime:
    secret_composition = (
        build_twilio_authenticated_read_secret_composition(
            authority=authority,
            api_key_sid_reference=api_key_sid_reference,
            api_key_secret_reference=api_key_secret_reference,
        )
    )

    transport = TwilioOfflineAuthenticatedReadTransport(
        secret_composition=secret_composition,
        secret_resolver=secret_resolver,
        executor=executor,
        normalizer=normalizer,
    )

    return TwilioAuthenticatedReadOfflineRuntime(
        secret_composition=secret_composition,
        transport=transport,
    )
