"""Process-local operator lifecycle. No HTTP control or deployment authority.

All module work, including owned background jobs, must acquire a lease. Closing
admission and draining leases precede resource cleanup. No data purge is defined.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import inspect
import math
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .composition import DESCRIPTORS, ModuleConfigurationError, resolve_selection


class LifecycleDenied(RuntimeError):
    pass


class DrainTimeout(LifecycleDenied):
    pass


async def _invoke(callback):
    if callback is not None:
        result = callback()
        if inspect.isawaitable(result):
            await result


@dataclass
class ModuleInstance:
    app: FastAPI
    start: Callable | None = None
    close: Callable | None = None


@dataclass
class _Slot:
    state: str = "DETACHED"
    active: int = 0
    instance: ModuleInstance | None = None
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)


class ModuleManager:
    def __init__(self, providers=None, *, descriptors=DESCRIPTORS):
        self.descriptors = tuple(descriptors)
        resolve_selection(tuple(d.module_id for d in self.descriptors), self.descriptors)
        self.providers = dict(providers or {})
        self.slots = {d.module_id: _Slot() for d in self.descriptors}
        if set(self.providers) - set(self.slots):
            raise ModuleConfigurationError("unknown provider registration")
        self._mutation = asyncio.Lock()

    def snapshot(self):
        return [{"module_id": d.module_id, "state": self.slots[d.module_id].state,
                 "active_work": self.slots[d.module_id].active,
                 "implementation": d.implementation} for d in self.descriptors]

    def _slot(self, name):
        if name not in self.slots:
            raise LifecycleDenied("unknown_module")
        return self.slots[name]

    @asynccontextmanager
    async def lease(self, name):
        slot = self._slot(name)
        async with slot.condition:
            if slot.state != "ATTACHED":
                raise LifecycleDenied("module_not_attached")
            slot.active += 1
            instance = slot.instance
        try:
            yield instance
        finally:
            async with slot.condition:
                slot.active -= 1
                slot.condition.notify_all()

    async def attach(self, name):
        async with self._mutation:
            slot = self._slot(name)
            if slot.state == "ATTACHED":
                return
            if slot.state not in {"DETACHED", "UNAVAILABLE", "BLOCKED"}:
                raise LifecycleDenied("module_transition_pending")
            descriptor = next(d for d in self.descriptors if d.module_id == name)
            if any(self._slot(dep).state != "ATTACHED" for dep in descriptor.requires):
                slot.state = "BLOCKED"
                return
            factory = self.providers.get(name)
            if factory is None:
                slot.state = "UNAVAILABLE"
                return
            slot.state = "ATTACHING"
            instance = None
            try:
                instance = factory()
                if inspect.isawaitable(instance):
                    instance = await instance
                if isinstance(instance, FastAPI):
                    instance = ModuleInstance(instance)
                if not isinstance(instance, ModuleInstance) or not isinstance(instance.app, FastAPI):
                    raise TypeError("invalid module instance")
                slot.instance = instance
                await asyncio.wait_for(_invoke(instance.start), 5.0)
            except (Exception, asyncio.CancelledError) as error:
                try:
                    if isinstance(instance, ModuleInstance):
                        await asyncio.wait_for(_invoke(instance.close), 5.0)
                    slot.instance = None
                    slot.state = "UNAVAILABLE"
                except (Exception, asyncio.CancelledError):
                    slot.state = "STOP_FAILED"
                if isinstance(error, asyncio.CancelledError):
                    raise
                return
            slot.state = "ATTACHED"

    async def detach(self, name, *, timeout=5.0):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("finite positive drain timeout required")
        async with self._mutation:
            slot = self._slot(name)
            if slot.state == "DETACHED":
                return
            if any(name in d.requires and self.slots[d.module_id].state not in
                   {"DETACHED", "UNAVAILABLE", "BLOCKED"} for d in self.descriptors):
                raise LifecycleDenied("attached_dependents_exist")
            if slot.instance is None:
                slot.state = "DETACHED"
                return
            async with slot.condition:
                slot.state = "DRAINING"
                try:
                    await asyncio.wait_for(slot.condition.wait_for(lambda: slot.active == 0), timeout)
                except TimeoutError:
                    # Admission remains closed. Never close resources used by active work.
                    raise DrainTimeout("module_drain_timeout") from None
            try:
                await asyncio.wait_for(_invoke(slot.instance.close), timeout)
            except (Exception, asyncio.CancelledError) as error:
                slot.state = "STOP_FAILED"
                if isinstance(error, asyncio.CancelledError):
                    raise
                raise LifecycleDenied("module_cleanup_failed") from None
            slot.instance = None
            slot.state = "DETACHED"


class ManagedBoundary:
    def __init__(self, manager, name):
        self.manager, self.name = manager, name

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            return
        if scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
            await JSONResponse({"detail": "module_read_only"}, status_code=405)(scope, receive, send)
            return
        # Catch admission errors only, not failures raised by an admitted handler.
        lease = self.manager.lease(self.name)
        try:
            instance = await lease.__aenter__()
        except LifecycleDenied:
            code = 404 if self.manager.slots[self.name].state == "DETACHED" else 503
            await JSONResponse({"detail": "module_unavailable"}, status_code=code)(scope, receive, send)
            return
        try:
            await instance.app(scope, receive, send)
        finally:
            await lease.__aexit__(None, None, None)


def create_managed_app(attached=(), *, providers=None, descriptors=DESCRIPTORS):
    descriptors = tuple(descriptors)
    order = resolve_selection(attached, descriptors)
    manager = ModuleManager(providers, descriptors=descriptors)

    @asynccontextmanager
    async def lifespan(app):
        try:
            for name in order:
                await manager.attach(name)
            yield
        finally:
            failures = []
            for name in reversed(resolve_selection(tuple(d.module_id for d in descriptors), descriptors)):
                try:
                    await manager.detach(name)
                except LifecycleDenied:
                    failures.append(name)
            if failures:
                raise LifecycleDenied("module_shutdown_incomplete")

    app = FastAPI(title="AIControlCenter managed module validation", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.module_manager = manager  # Trusted in-process operator use only.
    for descriptor in descriptors:
        app.mount("/extensions/" + descriptor.module_id,
                  ManagedBoundary(manager, descriptor.module_id), name=descriptor.module_id)

    @app.get("/health")
    def health():
        return {"service": "AIControlCenter", "status": "ONLINE", "profile": "managed_validation"}

    @app.get("/platform/modules")
    def modules():
        return {"schema_version": 1, "activation": "operator_in_process", "read_only": True,
                "modules": manager.snapshot()}

    from .plugin_catalog import add_plugin_catalog_route
    add_plugin_catalog_route(app, manager.snapshot)
    return app
