"""Compatibility exports for the pure, platform-owned offline composition.

No production behavior or authorization semantics change. Both import paths
resolve to exactly the same class, preserving strict identity checks.
"""
from core.shopping.adapters.twilio_authenticated_read_secret_composition import (
    TwilioAuthenticatedReadSecretComposition,
    build_twilio_authenticated_read_secret_composition,
)

__all__ = ("TwilioAuthenticatedReadSecretComposition", "build_twilio_authenticated_read_secret_composition")
