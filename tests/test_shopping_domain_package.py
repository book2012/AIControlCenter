from dataclasses import asdict
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("aicc_plugin_shopping", reason="optional shopping domain wheel required")


def test_product_and_order_compatibility_exports_keep_exact_class_identity():
    from aicc_plugin_shopping import models as package_models
    from core.shopping import models as host_models
    for name in ["Product", "ProductVariant"]:
        assert getattr(package_models, name) is getattr(host_models, name)
    from aicc_plugin_shopping import order_core as package_orders
    from core.shopping import order_core as host_orders
    for name in host_orders.__all__:
        assert getattr(package_orders, name) is getattr(host_orders, name)
    from core.shopping.order_core.service import OrderService as old_service
    assert old_service is package_orders.OrderService


def test_moved_order_service_still_rejects_untrusted_result_shape():
    from core.shopping.order_core import OrderService, OrderListQuery, OrderContractError
    class InvalidReader:
        def list_orders(self, query):
            return [{"provider_order_id": 1}]
        def read_order(self, order_id):
            return {"provider_order_id": order_id}
    service = OrderService(InvalidReader())
    with pytest.raises(OrderContractError):
        service.list_orders(OrderListQuery())
    with pytest.raises(OrderContractError):
        service.read_order(1)


def test_domain_imports_without_host_or_http_framework():
    import aicc_plugin_shopping
    installed_root = str(Path(aicc_plugin_shopping.__file__).resolve().parent.parent)
    code = """
import sys, builtins
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.split('.')[0] in {'core', 'ops', 'integrations', 'fastapi', 'requests', 'httpx', 'sqlite3'}:
        raise AssertionError('domain imported external dependency: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guard
from aicc_plugin_shopping.models import Product, ProductVariant
from aicc_plugin_shopping.order_core import OrderService, OrderSnapshot, OrderListQuery
from decimal import Decimal
from datetime import datetime, timezone
now = datetime(2026, 11, 3, tzinfo=timezone.utc)
order = OrderSnapshot('woocommerce', 1, 'fixture', 'fixture', 'processing', 'KRW', None,
    (), Decimal('19000.00'), Decimal('0.00'), now, now, 'fixture')
class Reader:
    def read_order(self, order_id):
        return order if order_id == 1 else None
    def list_orders(self, query):
        return (order,)
service = OrderService(Reader())
assert service.read_order(1) is order
assert service.list_orders(OrderListQuery()) == (order,)
assert not any(n.startswith(('core.', 'fastapi', 'integrations.')) for n in sys.modules)
"""
    result = subprocess.run([sys.executable, "-I", "-c", code, installed_root], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
