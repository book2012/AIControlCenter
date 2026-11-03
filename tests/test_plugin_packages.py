import importlib.util
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import zipfile

from fastapi.testclient import TestClient
import pytest

from scripts.build_plugin_wheels import ROOT, PACKAGES, build_wheel
from core.modules.composition import create_module_app
from core.modules.plugin_loader import plugin_providers


@pytest.mark.parametrize("plugin_id", list(PACKAGES))
def test_wheel_is_reproducible_and_record_matches_exact_files(tmp_path, plugin_id):
    first = build_wheel(plugin_id, tmp_path / "one")
    second = build_wheel(plugin_id, tmp_path / "two")
    assert first["sha256"] == second["sha256"]
    with zipfile.ZipFile(first["wheel"]) as archive:
        names = set(archive.namelist())
        record_name = next(x for x in names if x.endswith(".dist-info/RECORD"))
        rows = list(csv.reader(io.StringIO(archive.read(record_name).decode())))
        assert set(row[0] for row in rows) == names
        for name, digest, size in rows:
            if name == record_name:
                assert digest == size == ""
                continue
            data = archive.read(name)
            actual = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            assert digest == "sha256=" + actual
            assert int(size) == len(data)
        assert not any(x.endswith((".env", ".db", ".pyc")) for x in names)
        assert all(x.startswith((PACKAGES[plugin_id] + "/", PACKAGES[plugin_id] + "-" + first["version"] + ".dist-info/")) for x in names)
        assert not any(x.startswith("core/") for x in names)


@pytest.mark.parametrize("plugin_id", list(PACKAGES))
def test_each_wheel_installs_alone_and_other_absent_plugins_do_not_break_core(tmp_path, plugin_id):
    wheel = build_wheel(plugin_id, tmp_path / "dist")["wheel"]
    target = tmp_path / "installed"
    installed = subprocess.run([sys.executable, "-m", "pip", "--isolated", "--disable-pip-version-check",
        "install", "--no-index", "--no-deps", "--target", str(target), wheel], capture_output=True, text=True)
    assert installed.returncode == 0, installed.stderr
    code = """
import sys, json, sqlite3, socket
sys.path[:0] = [sys.argv[1], sys.argv[2]]
def forbidden(*a, **kw):
    raise AssertionError('unexpected external access')
sqlite3.connect = forbidden
socket.create_connection = forbidden
from fastapi.testclient import TestClient
from core.api.modular import create_managed_validation_app
from pathlib import Path
app = create_managed_validation_app(manifest_path=Path(sys.argv[1]) / 'config/modules/all-adapters.json')
with TestClient(app) as client:
    result = client.get('/platform/modules').json()['modules']
    states = {item['module_id']: item['state'] for item in result}
    assert states[sys.argv[3]] == 'ATTACHED', states
    assert all(v == 'UNAVAILABLE' for k,v in states.items() if k != sys.argv[3]), states
    assert client.get('/health').status_code == 200
    assert client.get('/extensions/' + sys.argv[3] + '/health').status_code == 200
assert 'core.api.app' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT), str(target), plugin_id],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_no_plugin_installation_required_for_detached_or_missing_selected_plugins():
    code = """
import sys, sqlite3, socket
sys.path.insert(0, sys.argv[1])
def forbidden(*a, **kw):
    raise AssertionError('unexpected access')
sqlite3.connect = forbidden
socket.create_connection = forbidden
from pathlib import Path
from fastapi.testclient import TestClient
from core.api.modular import create_app, create_managed_validation_app
with TestClient(create_app()) as client:
    assert client.get('/health').status_code == 200
    assert all(x['state'] == 'DETACHED' for x in client.get('/platform/modules').json()['modules'])
app = create_managed_validation_app(manifest_path=Path(sys.argv[1]) / 'config/modules/all-adapters.json')
with TestClient(app) as client:
    assert client.get('/health').status_code == 200
    assert all(x['state'] == 'UNAVAILABLE' for x in client.get('/platform/modules').json()['modules'])
assert not any(n.startswith('aicc_plugin_') for n in sys.modules)
assert 'core.api.app' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("api", [None, True, 0, 2, "1"])
def test_incompatible_plugin_api_fails_only_selected_plugin(monkeypatch, api):
    fake = types.ModuleType("aicc_plugin_shopping")
    fake.PLATFORM_PLUGIN_API = api
    monkeypatch.setitem(sys.modules, "aicc_plugin_shopping", fake)
    app = create_module_app(["shopping"], providers=plugin_providers(["shopping"]))
    with TestClient(app) as client:
        states = {x['module_id']: x['state'] for x in client.get('/platform/modules').json()['modules']}
        assert states['shopping'] == 'UNAVAILABLE'
        assert client.get('/health').status_code == 200


@pytest.mark.skipif(importlib.util.find_spec("aicc_plugin_shopping") is None, reason="optional shopping wheel required")
def test_binding_compatibility_is_exact_class_identity():
    from aicc_plugin_shopping import ShoppingBindings as moved
    from core.modules.shopping_bindings import ShoppingBindings as compatibility
    assert moved is compatibility
