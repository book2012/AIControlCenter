"""Compatibility facade; secret-delivery composition is owned by Core."""
from core.shopping.adapters.twilio_authenticated_read_secret_composition import (
    TwilioAuthenticatedReadSecretComposition,
    build_twilio_authenticated_read_secret_composition,
)

__all__ = ("TwilioAuthenticatedReadSecretComposition", "build_twilio_authenticated_read_secret_composition")
