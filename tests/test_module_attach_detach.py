import json
from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.modules.composition import (
    ModuleConfigurationError, ModuleDescriptor, create_module_app,
    load_selection, resolve_selection,
)
from core.api.modular import create_app


def states(app):
    return {x["module_id"]: x["state"] for x in TestClient(app).get("/platform/modules").json()["modules"]}


def provider():
    app = FastAPI()
    @app.get("/ping")
    def ping():
        return {"ok": True}
    @app.post("/mutate")
    def mutate():
        raise AssertionError("write handler must never be entered")
    return app


def test_default_detached_keeps_core_and_has_no_shopping_routes():
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/extensions/shopping/health").status_code == 404
        assert client.get("/shopping/products").status_code == 404
    assert set(states(app).values()) == {"DETACHED"}


def test_reattach_detach_generations_do_not_delete_data(tmp_path):
    retained = tmp_path / "owned-data.json"
    retained.write_text('{"order":"keep"}')
    first = create_module_app(["shopping"], providers={"shopping": provider})
    detached = create_module_app([])
    last = create_module_app(["shopping"], providers={"shopping": provider})
    for app, expected in [(first, 200), (detached, 404), (last, 200)]:
        with TestClient(app) as client:
            assert client.get("/extensions/shopping/ping").status_code == expected
            assert client.get("/health").status_code == 200
    assert retained.read_text() == '{"order":"keep"}'


def test_detached_factory_never_runs():
    def forbidden():
        raise AssertionError("detached factory called")
    assert states(create_module_app([], providers={"shopping": forbidden}))["shopping"] == "DETACHED"


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_write_methods_never_reach_provider(method):
    client = TestClient(create_module_app(["shopping"], providers={"shopping": provider}))
    assert getattr(client, method)("/extensions/shopping/mutate").status_code == 405


def test_factory_failure_does_not_disable_other_module_or_leak_secrets():
    def broken():
        raise RuntimeError("secret credential must not appear")
    app = create_module_app(["shopping", "personal-assistant"],
        providers={"shopping": broken, "personal-assistant": provider})
    client = TestClient(app)
    result = client.get("/platform/modules")
    assert "secret credential" not in result.text
    assert states(app)["shopping"] == "UNAVAILABLE"
    assert client.get("/extensions/personal-assistant/ping").status_code == 200
    assert client.get("/extensions/shopping/ping").status_code == 404
    assert client.get("/health").status_code == 200


def test_missing_implementation_is_honest():
    app = create_module_app(["creative-notes"])
    assert states(app)["creative-notes"] == "UNAVAILABLE"


@pytest.mark.parametrize("selection", [["unknown"], ["shopping", "shopping"], "shopping", [1]])
def test_invalid_selection_rejected_before_factories(selection):
    calls = []
    with pytest.raises(ModuleConfigurationError):
        create_module_app(selection, providers={"shopping": lambda: calls.append(1)})
    assert calls == []


def test_dependency_order_and_blocked_dependents():
    descriptors = (ModuleDescriptor("child", ("parent",)), ModuleDescriptor("parent"))
    assert resolve_selection(["child", "parent"], descriptors) == ("parent", "child")
    calls = []
    app = create_module_app(["child", "parent"], descriptors=descriptors,
        providers={"child": lambda: calls.append(1)})
    assert states(app) == {"child": "BLOCKED", "parent": "UNAVAILABLE"}
    assert calls == []


def test_missing_dependency_is_not_implicitly_attached():
    with pytest.raises(ModuleConfigurationError):
        resolve_selection(["child"], (ModuleDescriptor("child", ("parent",)), ModuleDescriptor("parent")))


def test_cycle_rejected():
    with pytest.raises(ModuleConfigurationError):
        resolve_selection(["a", "b"], (ModuleDescriptor("a", ("b",)), ModuleDescriptor("b", ("a",))))


@pytest.mark.parametrize("payload", [
    '{}', '{"schema_version":true,"attached":[]}',
    '{"schema_version":2,"attached":[]}',
    '{"schema_version":1,"attached":[],"import":"os.system"}',
    '{"schema_version":1,"attached":[1]}',
    '{"schema_version":1,"attached":[],"attached":["shopping"]}',
    '[]', 'not-json',
])
def test_manifest_fail_closed(tmp_path, payload):
    path = tmp_path / "manifest.json"
    path.write_text(payload)
    with pytest.raises(ModuleConfigurationError):
        load_selection(path)


def test_unreadable_manifest_rejected(tmp_path):
    with pytest.raises(ModuleConfigurationError):
        load_selection(tmp_path / "missing.json")


def test_no_import_or_database_access_when_detached_in_fresh_process():
    code = """
import builtins, sqlite3, socket, subprocess, sys
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.startswith(('core.shopping', 'core.api.app', 'core.homepage')):
        raise AssertionError('disabled domain imported: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guard
def forbidden(*a, **kw):
    raise AssertionError('external access')
sqlite3.connect = forbidden
socket.create_connection = forbidden
subprocess.Popen = forbidden
from core.api.modular import create_app
app = create_app()
assert not any(n.startswith('core.shopping') for n in sys.modules)
assert {route.path for route in app.routes} == {"/health", "/platform/modules", "/platform/plugins"}
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1])
    assert result.returncode == 0, result.stderr


def test_real_shopping_preview_reads_without_external_access(monkeypatch):
    import sqlite3
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("DB or network access forbidden")
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setenv("SHOPPING_CATALOG_ADAPTER", "woocommerce")
    monkeypatch.setenv("SHOPPING_WRITE_MODE", "automated")
    monkeypatch.setenv("AICONTROLCENTER_SHOPPING_PROFILE", "woocommerce_read_only")
    app = create_app(manifest_path=Path(__file__).resolve().parents[1] / "config/modules/shopping-preview.json")
    assert states(app)["shopping"] == "ATTACHED"
    with TestClient(app) as client:
        health = client.get("/extensions/shopping/health")
        assert health.status_code == 200
        assert health.json()["write_mode"] == "read_only"
        assert health.json()["environment"] == "isolated_preview"
        products = client.get("/extensions/shopping/products")
        assert products.status_code == 200
        assert client.get("/extensions/shopping/products?page=0").status_code == 422
        assert client.get("/extensions/shopping/products/not-found").status_code == 404
        assert client.post("/extensions/shopping/orders").status_code == 405
        assert client.get("/extensions/shopping/inquiries").status_code == 404
        assert client.get("/health").status_code == 200


def test_module_exception_does_not_break_core():
    def faulting():
        app = FastAPI()
        @app.get("/fail")
        def fail():
            raise RuntimeError("provider failure")
        return app
    client = TestClient(create_module_app(["shopping"], providers={"shopping": faulting}),
                        raise_server_exceptions=False)
    assert client.get("/extensions/shopping/fail").status_code == 500
    assert client.get("/health").status_code == 200


def test_status_is_snapshot_and_cannot_change_selection():
    client = TestClient(create_module_app(["shopping"], providers={"shopping": provider}))
    first = client.get("/platform/modules").json()
    assert client.post("/platform/modules", json={"attached": []}).status_code == 405
    assert client.get("/platform/modules").json() == first


@pytest.mark.parametrize("module_id", ["../health", "x/y", "", "UPPER", "x" * 49])
def test_invalid_registered_paths_cannot_escape_namespace(module_id):
    with pytest.raises(ModuleConfigurationError):
        create_module_app([], descriptors=(ModuleDescriptor(module_id),))


def test_duplicate_registration_rejected():
    with pytest.raises(ModuleConfigurationError):
        create_module_app([], descriptors=(ModuleDescriptor("a"), ModuleDescriptor("a")))


def test_unknown_provider_rejected():
    with pytest.raises(ModuleConfigurationError):
        create_module_app([], providers={"unknown": provider})


def test_wrong_provider_return_type_is_unavailable():
    assert states(create_module_app(["shopping"], providers={"shopping": lambda: object()}))["shopping"] == "UNAVAILABLE"


def test_websocket_is_not_a_write_bypass():
    from starlette.websockets import WebSocketDisconnect
    client = TestClient(create_module_app(["shopping"], providers={"shopping": provider}))
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect("/extensions/shopping/socket"):
            pass
    assert error.value.code == 1008


def test_plan_cli_never_applies_or_attaches():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-m", "scripts.module_plan",
        "config/modules/shopping-preview.json"], cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["mode"] == "PLAN_ONLY"
    assert value["attached_requested"] == ["shopping"]
    assert not value["data_deletion"] and not value["production_activation"]
