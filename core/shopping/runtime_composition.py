"""Application-owned Shopping runtime composition."""
from __future__ import annotations

from dataclasses import dataclass

from core.secrets.ports import SecretResolverPort
from .adapters.phone_verification import ProviderPhoneVerificationAdapter
from .config import ShoppingSettings
from .ports.destination_resolution import DestinationResolutionPort
from .ports.phone_verification import PhoneVerificationPort
from .ports.phone_verification_transport import ProviderTransportPort
from .product_drafts.read import ProductDraftQueryService
from .product_drafts.runtime import ProductDraftCapability, build_product_draft_read_runtime
from .secure_runtime import build_default_shopping_service
from .service import ShoppingService


@dataclass(frozen=True, slots=True)
class FutureProviderComposition:
    """Non-activating seam for a future provider-specific outer transport."""

    provider_profile: str
    provider_transport: ProviderTransportPort
    destination_resolution: DestinationResolutionPort
    secret_resolver: SecretResolverPort


@dataclass(frozen=True, slots=True)
class ShoppingRuntime:
    catalog_service: ShoppingService
    product_draft_query_service: ProductDraftQueryService
    product_draft_capability: ProductDraftCapability
    product_draft_mutation_available: bool = False
    phone_verification_port: PhoneVerificationPort | None = None
    destination_resolution: DestinationResolutionPort | None = None
    secret_resolver: SecretResolverPort | None = None
    future_provider_composition: FutureProviderComposition | None = None

    @property
    def phone_verification(self) -> PhoneVerificationPort | None:
        """Optional internal capability; it is absent in default composition."""

        return self.phone_verification_port

    @property
    def destination_resolution_port(self) -> DestinationResolutionPort | None:
        return self.destination_resolution


def build_shopping_runtime(
    settings: ShoppingSettings | None = None,
    *,
    phone_verification_transport: ProviderTransportPort | None = None,
    destination_resolution: DestinationResolutionPort | None = None,
    secret_resolver: SecretResolverPort | None = None,
    phone_verification_destination_resolution: DestinationResolutionPort | None = None,
    phone_verification_secret_resolver: SecretResolverPort | None = None,
    future_provider_composition: FutureProviderComposition | None = None,
) -> ShoppingRuntime:
    if destination_resolution is not None and phone_verification_destination_resolution is not None:
        raise ValueError("choose one destination resolution port")
    if secret_resolver is not None and phone_verification_secret_resolver is not None:
        raise ValueError("choose one secret resolver")
    if destination_resolution is None:
        destination_resolution = phone_verification_destination_resolution
    if secret_resolver is None:
        secret_resolver = phone_verification_secret_resolver
    product_drafts = build_product_draft_read_runtime()
    phone_verification_port: PhoneVerificationPort | None = None
    # Construction is deliberately opt-in twice: a named profile must be
    # enabled and a transport must be supplied by a future composition path.
    # Thus the ordinary runtime constructs neither adapter nor transport.
    if (
        settings is not None
        and settings.phone_verification_enabled
        and settings.phone_verification_profile is not None
        and settings.phone_verification_profile.strip().lower()
        not in {"", "disabled", "off", "none"}
        and phone_verification_transport is not None
    ):
        adapter_kwargs = dict(
            transport=phone_verification_transport,
            provider_source=settings.phone_verification_profile,
            secret_reference=settings.phone_verification_secret_reference,
            timeout_seconds=settings.phone_verification_timeout_seconds,
        )
        phone_verification_port = ProviderPhoneVerificationAdapter(**adapter_kwargs)
    return ShoppingRuntime(
        catalog_service=build_default_shopping_service(),
        product_draft_query_service=product_drafts.query_service,
        product_draft_capability=product_drafts.capability,
        phone_verification_port=phone_verification_port,
        destination_resolution=destination_resolution,
        secret_resolver=secret_resolver,
        future_provider_composition=future_provider_composition,
    )


__all__ = (
    "FutureProviderComposition", "ShoppingRuntime", "build_shopping_runtime",
)
