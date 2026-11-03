"""Trusted composition of an existing shopping store into the managed lifecycle."""
from fastapi import FastAPI
from .lifecycle import ModuleInstance


def storage_module_instance(database_path, *, data_root, application_factory, channel_provider=None):
    """Construction performs no I/O. Caller supplies authenticated application code."""
    from aicc_plugin_shopping.storage_resource import ShoppingStorageResource
    resource = ShoppingStorageResource(database_path, data_root=data_root, channel_provider=channel_provider)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def start():
        resource.start()
        child = application_factory(resource)
        if not isinstance(child, FastAPI):
            raise TypeError("trusted application factory must return FastAPI")
        app.mount("/", child)

    def close():
        app.router.routes.clear()
        resource.close()

    return ModuleInstance(app, start=start, close=close)
