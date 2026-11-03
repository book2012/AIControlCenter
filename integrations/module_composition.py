"""Outer composition supplies replaceable providers to the core module host."""
from core.api.modular import create_managed_validation_app
from core.capabilities.service import CapabilityStatusService
from integrations.openclaw.adapter import OpenClawAdapter, OpenClawConfiguration


def create_validation_app(*, manifest_path=None, shopping_bindings=None):
    return create_managed_validation_app(manifest_path=manifest_path,
        shopping_bindings=shopping_bindings,
        personal_assistant_status=CapabilityStatusService(
            OpenClawAdapter(OpenClawConfiguration())))
