"""Startup-only, read-only module attachment. No runtime deployment authority."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from fastapi import FastAPI
from fastapi.responses import JSONResponse


class ModuleConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ModuleDescriptor:
    module_id: str
    requires: tuple[str, ...] = ()
    implementation: str = "not_integrated"


DESCRIPTORS = (
    ModuleDescriptor("shopping", implementation="catalog_preview"),
    ModuleDescriptor("creative-notes"),
    ModuleDescriptor("personal-assistant"),
)


def load_selection(path: str | Path) -> tuple[str, ...]:
    """Strict data-only manifest. Never import a manifest-specified Python path."""
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ModuleConfigurationError("duplicate manifest field")
            result[key] = value
        return result
    try:
        value = json.loads(Path(path).read_text(), object_pairs_hook=unique_pairs)
    except (OSError, ValueError, TypeError) as error:
        raise ModuleConfigurationError("module manifest unavailable or invalid") from None
    if (not isinstance(value, dict) or set(value) != {"schema_version", "attached"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or not isinstance(value["attached"], list)
            or any(type(item) is not str for item in value["attached"])):
        raise ModuleConfigurationError("invalid module manifest")
    return tuple(value["attached"])


def resolve_selection(attached, descriptors=DESCRIPTORS) -> tuple[str, ...]:
    """Validate the entire graph before any provider construction."""
    descriptors = tuple(descriptors)
    if any(not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", item.module_id) for item in descriptors):
        raise ModuleConfigurationError("invalid registered module ID")
    by_id = {item.module_id: item for item in descriptors}
    if len(by_id) != len(descriptors):
        raise ModuleConfigurationError("duplicate registered module")
    if not isinstance(attached, (tuple, list)) or any(type(x) is not str for x in attached):
        raise ModuleConfigurationError("attached must be a sequence of module IDs")
    if len(set(attached)) != len(attached) or any(x not in by_id for x in attached):
        raise ModuleConfigurationError("unknown or duplicate module selection")
    selected = set(attached)
    ordered, visiting, visited = [], set(), set()
    def visit(name):
        if name in visiting:
            raise ModuleConfigurationError("module dependency cycle")
        if name in visited:
            return
        visiting.add(name)
        for dependency in by_id[name].requires:
            if dependency not in selected:
                raise ModuleConfigurationError("attached dependency is missing")
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        ordered.append(name)
    for name in attached:
        visit(name)
    return tuple(ordered)


class ReadOnlyBoundary:
    """A module cannot expose mutations through the preview composition."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] == "http" and scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
            await JSONResponse({"detail": "module_read_only"}, status_code=405)(scope, receive, send)
            return
        await self.app(scope, receive, send)


def create_module_app(
    attached=(), *, providers: Mapping[str, Callable[[], FastAPI]] | None = None,
    descriptors=DESCRIPTORS,
) -> FastAPI:
    """Compose immutable routes before serving. Detach means a new app generation.

    Providers must construct stateless read adapters only. They may not start
    threads, jobs, clients with unmanaged resources, or subprocesses. The
    manifest is configuration, never authorization to access production.
    """
    descriptors = tuple(descriptors)
    order = resolve_selection(attached, descriptors)
    supplied = dict(providers or {})
    known = {item.module_id for item in descriptors}
    if any(key not in known for key in supplied):
        raise ModuleConfigurationError("unknown provider registration")
    app = FastAPI(title="AIControlCenter modular preview", docs_url=None, redoc_url=None,
                  openapi_url=None)
    states = {item.module_id: {"module_id": item.module_id, "state": "DETACHED",
              "implementation": item.implementation} for item in descriptors}
    by_id = {item.module_id: item for item in descriptors}
    for name in order:
        if any(states[dep]["state"] != "ATTACHED" for dep in by_id[name].requires):
            states[name]["state"] = "BLOCKED"
            continue
        factory = supplied.get(name)
        if factory is None:
            states[name]["state"] = "UNAVAILABLE"
            continue
        try:
            module_app = factory()
            if not isinstance(module_app, FastAPI):
                raise TypeError("module must provide a FastAPI application")
        except Exception:
            states[name]["state"] = "UNAVAILABLE"
            continue
        app.mount("/extensions/" + name, ReadOnlyBoundary(module_app), name=name)
        states[name]["state"] = "ATTACHED"

    # Capture plain data only. Status never calls a provider or a remote health probe.
    snapshot = tuple(dict(states[item.module_id]) for item in descriptors)

    @app.get("/health")
    def health():
        return {"service": "AIControlCenter", "status": "ONLINE", "profile": "modular_preview"}

    @app.get("/platform/modules")
    def modules():
        return {"schema_version": 1, "activation": "startup_only", "read_only": True,
                "modules": [dict(item) for item in snapshot]}

    return app
