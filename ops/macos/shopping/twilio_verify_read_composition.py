from __future__ import annotations

from dataclasses import dataclass

from core.shopping.ports.provider_activation import (
    ProviderActivationState,
)

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioReadRequestSpec,
    TwilioServiceSid,
    TwilioVerificationSid,
    build_service_read_request,
    build_verification_read_request,
)


@dataclass(frozen=True, slots=True)
class TwilioVerifyReadComposition:
    """Offline C5-C2 composition; no transport or credentials exist."""

    service_sid: TwilioServiceSid
    activation_state: ProviderActivationState = (
        ProviderActivationState.CONTRACT_ONLY
    )
    transport_constructed: bool = False
    credential_resolution_performed: bool = False

    def __post_init__(self) -> None:
        if type(self.service_sid) is not TwilioServiceSid:
            raise TypeError("Twilio service SID is required")

        if (
            self.activation_state
            is not ProviderActivationState.CONTRACT_ONLY
        ):
            raise ValueError(
                "C5-C2 composition must remain CONTRACT_ONLY"
            )

        if self.transport_constructed is not False:
            raise ValueError(
                "C5-C2 transport construction is forbidden"
            )

        if self.credential_resolution_performed is not False:
            raise ValueError(
                "C5-C2 credential resolution is forbidden"
            )

    @property
    def provider_source(self) -> str:
        return TWILIO_PROVIDER_SOURCE

    @property
    def authorization_model(self) -> str:
        return "OFFLINE_DENY_ONLY"

    @property
    def network_enabled(self) -> bool:
        return False

    def service_request(self) -> TwilioReadRequestSpec:
        return build_service_read_request(
            self.service_sid
        )

    def verification_request(
        self,
        verification_sid: TwilioVerificationSid,
    ) -> TwilioReadRequestSpec:
        return build_verification_read_request(
            self.service_sid,
            verification_sid,
        )

    def __repr__(self) -> str:
        return (
            "TwilioVerifyReadComposition("
            "provider='twilio.verify.v2', "
            "activation_state='CONTRACT_ONLY', "
            "network_enabled=False)"
        )


def build_twilio_verify_read_composition(
    *,
    service_sid: str | TwilioServiceSid,
) -> TwilioVerifyReadComposition:
    sid = (
        service_sid
        if type(service_sid) is TwilioServiceSid
        else TwilioServiceSid(service_sid)
    )

    return TwilioVerifyReadComposition(
        service_sid=sid,
    )
