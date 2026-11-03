"""Outer composition supplies replaceable providers to the core module host."""
from core.api.modular import create_managed_validation_app
from core.capabilities.service import CapabilityStatusService
from integrations.openclaw.adapter import OpenClawAdapter, OpenClawConfiguration


def create_validation_app(*, manifest_path=None, shopping_bindings=None):
    return create_managed_validation_app(manifest_path=manifest_path,
        shopping_bindings=shopping_bindings,
        personal_assistant_status=CapabilityStatusService(
            OpenClawAdapter(OpenClawConfiguration())))


def create_shopping_on_demand_instance(application_factory, *, controller):
    """Opt-in trusted composition. Never selected by the default plugin loader."""
    import asyncio
    from fastapi import FastAPI
    from core.modules.lifecycle import ModuleInstance
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    async def start():
        await asyncio.to_thread(controller.apply, "attach")
        child = application_factory()
        if not isinstance(child, FastAPI):
            raise TypeError("application factory must return FastAPI")
        app.mount("/", child)
    async def close():
        app.router.routes.clear()
        await asyncio.to_thread(controller.apply, "detach")
    return ModuleInstance(app, start=start, close=close)
