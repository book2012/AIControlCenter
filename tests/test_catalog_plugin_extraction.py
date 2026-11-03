from dataclasses import fields
import importlib
from pathlib import Path
import subprocess
import sys

import pytest
pytest.importorskip("aicc_plugin_shopping", reason="optional shopping plugin required")


def test_catalog_operates_without_host_or_ambient_configuration():
    import aicc_plugin_shopping
    installed = str(Path(aicc_plugin_shopping.__file__).resolve().parent.parent)
    code = """
import sys, builtins, os
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.split('.')[0] in {'core', 'ops', 'integrations', 'fastapi', 'requests', 'httpx', 'sqlite3'}:
        raise AssertionError('forbidden catalog dependency: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guard
from aicc_plugin_shopping.catalog_settings import CatalogSettings
from aicc_plugin_shopping.catalog_service import ShoppingService, ProductNotFoundError
from aicc_plugin_shopping.adapters.mock_commerce import MockCommerceCatalogAdapter
from aicc_plugin_shopping.catalog_ports import CatalogReadQueryError
service = ShoppingService(CatalogSettings(), MockCommerceCatalogAdapter())
assert service.list_products(1, 2)['items'][0]['price'] == '29.90'
assert service.get_product('mock-001')['id'] == 'mock-001'
assert service.list_categories()['total'] > 0
assert service.search_products(query='Shopping', category=None, minimum_price=None,
    maximum_price=None, in_stock=None, page=1, page_size=20)['total'] > 0
assert service.list_featured_products(2)['total'] == 2
assert service.read_path_health()['healthy'] is True
assert service.read_path_telemetry().total == 3
try:
    service.list_products(0, 20)
except CatalogReadQueryError:
    pass
else:
    raise AssertionError('query validation lost')
try:
    service.get_product('not-found')
except ProductNotFoundError:
    pass
else:
    raise AssertionError('not-found behavior lost')
"""
    result = subprocess.run([sys.executable, "-I", "-c", code, installed], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_standalone_preview_never_loads_host_config_or_contacts_network():
    import aicc_plugin_shopping
    installed = str(Path(aicc_plugin_shopping.__file__).resolve().parent.parent)
    code = """
import sys, builtins, socket, sqlite3
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guard(name, *args, **kwargs):
    if kwargs.get('level', args[3] if len(args) > 3 else 0) == 0 and name.split('.')[0] in {'core', 'ops', 'integrations'}:
        raise AssertionError('preview imported host: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guard
def forbidden(*a, **kw):
    raise AssertionError('network or DB access')
socket.create_connection = forbidden
sqlite3.connect = forbidden
from fastapi.testclient import TestClient
from aicc_plugin_shopping import create_shopping_preview
with TestClient(create_shopping_preview()) as client:
    assert client.get('/health').status_code == 200
    assert client.get('/products').json()['total'] == 5
    assert client.get('/products/mock-001').json()['price'] == '29.90'
    assert client.get('/products/unknown').status_code == 404
    assert client.get('/products?page=0').status_code == 422
    assert client.post('/products').status_code == 405
assert not any(n == 'core' or n.startswith('core.') for n in sys.modules)
"""
    result = subprocess.run([sys.executable, "-I", "-c", code, installed], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_plugin_constructor_has_no_ambient_fallback():
    from aicc_plugin_shopping.catalog_service import ShoppingService
    from aicc_plugin_shopping.catalog_settings import CatalogSettings
    with pytest.raises(TypeError):
        ShoppingService()
    with pytest.raises(TypeError):
        ShoppingService(CatalogSettings(), None)


def test_host_bridge_projects_only_public_settings_and_keeps_factory_selection(monkeypatch):
    import core.shopping.service as bridge
    from core.shopping.config import ShoppingSettings
    from aicc_plugin_shopping.adapters.mock_commerce import MockCommerceCatalogAdapter
    from aicc_plugin_shopping.catalog_service import ShoppingService
    captured = []
    adapter = MockCommerceCatalogAdapter()
    def factory(name, **kwargs):
        captured.append((name, kwargs))
        return adapter
    monkeypatch.setattr(bridge, "create_catalog_adapter", factory)
    settings = ShoppingSettings(True, "fixture", "virtual", "mac-mini-m4", "read_only", True, False, False,
        catalog_adapter="woocommerce", woocommerce_base_url="https://fixture.invalid",
        woocommerce_consumer_key="fixture-private-key", woocommerce_consumer_secret="fixture-private-secret")
    service = bridge.ShoppingService(settings)
    assert isinstance(service, ShoppingService)
    assert captured[0][0] == "woocommerce"
    assert captured[0][1]['woocommerce_consumer_secret'] == 'fixture-private-secret'
    assert not hasattr(service.settings, "woocommerce_consumer_key")
    assert not hasattr(service.settings, "woocommerce_consumer_secret")
    assert not hasattr(service.settings, "woocommerce_base_url")
    assert 'fixture-private' not in repr(service.settings)
    assert service.get_product("mock-001")['price'] == '29.90'


@pytest.mark.parametrize("suffix", ["schemas", "observability.health_probe", "observability.health_monitor",
    "observability.read_telemetry", "contracts.provisional", "adapters.mock_commerce"])
def test_host_module_alias_is_exact_implementation_module(suffix):
    assert importlib.import_module('core.shopping.' + suffix) is importlib.import_module('aicc_plugin_shopping.' + suffix)


def test_catalog_errors_and_port_identity_remain_compatible():
    from core.shopping.ports import CatalogReadUnavailable as old_error, CommerceCatalogPort as old_port
    from aicc_plugin_shopping.catalog_ports import CatalogReadUnavailable, CommerceCatalogPort
    from core.shopping.service import ProductNotFoundError as old_missing
    from aicc_plugin_shopping.catalog_service import ProductNotFoundError
    assert old_error is CatalogReadUnavailable
    assert old_port is CommerceCatalogPort
    assert old_missing is ProductNotFoundError
    from core.shopping.ports import Product as old_product, HealthFailureCode as old_health
    from aicc_plugin_shopping.models import Product
    from aicc_plugin_shopping.observability.health_probe import HealthFailureCode
    assert old_product is Product
    assert old_health is HealthFailureCode
