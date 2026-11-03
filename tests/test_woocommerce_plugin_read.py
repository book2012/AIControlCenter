from copy import deepcopy
import importlib
from pathlib import Path
import subprocess
import sys

import pytest
pytest.importorskip("aicc_plugin_shopping", reason="optional shopping plugin required")
from aicc_plugin_shopping.adapters.woocommerce_product_read import WooCommerceProductReadAdapter, WooCommerceAPIError
from aicc_plugin_shopping.catalog_ports import CatalogReadQueryError
from aicc_plugin_shopping.observability.health_probe import HealthFailureCode

PRODUCT = {"id": 42, "name": "fixture", "price": "25000.00", "stock_status": "instock", "status": "publish",
           "meta_data": [{"private": "fixture-secret"}]}


class Response:
    def __init__(self, payload, status=200, total="1"):
        self.payload, self.status_code = payload, status
        self.headers = {"X-WP-Total": total}
    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return deepcopy(self.payload)


class Port:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
    def read(self, path, *, params):
        self.calls.append((path, dict(params)))
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def test_product_reads_and_health_use_bounded_single_port_calls():
    port = Port(Response([PRODUCT]), Response(PRODUCT), Response([PRODUCT]))
    approvals = []
    def approve(path, query):
        approvals.append((path, dict(query)))
        query['status'] = 'draft'  # Approval cannot rewrite the request.
        return True
    adapter = WooCommerceProductReadAdapter(port, authorize=approve)
    products, total = adapter.list_products(1, 20)
    assert total == 1 and products[0].id == '42'
    assert str(products[0].price) == '25000'
    assert 'fixture-secret' not in repr(products)
    assert adapter.get_product('42').id == '42'
    assert adapter.health()['transport'] == 'injected'
    assert len(port.calls) == len(approvals) == 3
    assert port.calls[0][1]['status'] == 'publish'
    assert port.calls[2][1]['per_page'] == 1


@pytest.mark.parametrize('approval', [False, None, 1, 'yes'])
def test_denied_or_nonboolean_approval_never_reads(approval):
    port = Port()
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: approval)
    with pytest.raises(WooCommerceAPIError) as error:
        adapter.get_product('42')
    assert error.value.failure_code is HealthFailureCode.AUTHORIZATION
    assert port.calls == []


def test_authorizer_exception_is_sanitized_before_port_access():
    def denied(path, query):
        raise RuntimeError('fixture-secret')
    port = Port()
    adapter = WooCommerceProductReadAdapter(port, authorize=denied)
    with pytest.raises(WooCommerceAPIError) as error:
        adapter.list_products(1, 20)
    assert 'fixture-secret' not in str(error.value)
    assert port.calls == []


@pytest.mark.parametrize('identifier', ['', '0', '042', '../orders/1', '4?x', '４２', '1' * 21])
def test_invalid_identity_does_not_authorize_or_read(identifier):
    approvals = []
    port = Port()
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: approvals.append(1))
    with pytest.raises(CatalogReadQueryError):
        adapter.get_product(identifier)
    assert approvals == [] and port.calls == []


@pytest.mark.parametrize('page,size', [(0, 20), (True, 20), (1, 101), (1, 0)])
def test_invalid_pagination_rejected_before_authorization(page, size):
    port = Port()
    approvals = []
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: approvals.append(1))
    with pytest.raises(CatalogReadQueryError):
        adapter.list_products(page, size)
    assert approvals == [] and port.calls == []


@pytest.mark.parametrize('path,query', [('/orders/1', {}), ('/products/categories', {}),
    ('/products', {'consumer_key': 'fixture'}), ('/products', {'Authorization': 'fixture'}), ('/products?x', {})])
def test_new_product_adapter_cannot_be_used_as_generic_vendor_request(path, query):
    port = Port()
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: True)
    with pytest.raises(WooCommerceAPIError):
        adapter._request(path, query)
    assert port.calls == []
    assert not hasattr(adapter, 'get_order_summary_raw')


@pytest.mark.parametrize('status,code', [(401, HealthFailureCode.AUTHENTICATION), (403, HealthFailureCode.AUTHORIZATION),
    (429, HealthFailureCode.RATE_LIMIT), (500, HealthFailureCode.DEPENDENCY_UNAVAILABLE),
    (None, HealthFailureCode.DEPENDENCY_UNAVAILABLE), ([], HealthFailureCode.DEPENDENCY_UNAVAILABLE)])
def test_failures_are_normalized_without_retry(status, code):
    port = Port(Response({'secret': 'fixture-secret'}, status=status))
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: True)
    with pytest.raises(WooCommerceAPIError) as error:
        adapter.get_product('42')
    assert error.value.failure_code is code
    assert 'fixture-secret' not in str(error.value)
    assert len(port.calls) == 1


@pytest.mark.parametrize('failure', [RuntimeError('fixture-secret'), TimeoutError('fixture-secret'),
    WooCommerceAPIError('fixture-secret', failure_code=HealthFailureCode.TIMEOUT)])
def test_raw_port_exception_and_context_are_not_exposed(failure):
    port = Port(failure)
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: True)
    with pytest.raises(WooCommerceAPIError) as error:
        adapter.get_product('42')
    assert str(error.value) == 'WooCommerce request failed'
    assert error.value.__context__ is None
    assert len(port.calls) == 1


def test_not_found_and_private_visibility_are_not_public_products():
    port = Port(Response({}, status=404), Response({**PRODUCT, 'status': 'private'}))
    adapter = WooCommerceProductReadAdapter(port, authorize=lambda p, q: True)
    assert adapter.get_product('42') is None
    assert adapter.get_product('42') is None
    assert len(port.calls) == 2


def test_host_error_and_normalizer_identity_preserved():
    from core.shopping.adapters.woocommerce_rest import WooCommerceRESTAdapter, WooCommerceAPIError as old_error
    assert old_error is WooCommerceAPIError
    assert issubclass(WooCommerceRESTAdapter, WooCommerceProductReadAdapter)
    assert WooCommerceRESTAdapter._to_variants is WooCommerceProductReadAdapter._to_variants


def test_product_adapter_runs_without_host_requests_or_web_framework():
    import aicc_plugin_shopping
    installed = str(Path(aicc_plugin_shopping.__file__).resolve().parent.parent)
    code = """
import sys,builtins
sys.path.insert(0,sys.argv[1])
original=builtins.__import__
def guard(name,*args,**kwargs):
    if kwargs.get('level',args[3] if len(args)>3 else 0)==0 and name.split('.')[0] in {'core','ops','integrations','requests','fastapi','pydantic','sqlite3'}:
        raise AssertionError('unexpected dependency: '+name)
    return original(name,*args,**kwargs)
builtins.__import__=guard
from aicc_plugin_shopping.adapters.woocommerce_product_read import WooCommerceProductReadAdapter
class Response:
    status_code=200
    headers={}
    def json(self):
        return {'id':42,'name':'fixture','price':'19.00','stock_status':'instock','status':'publish'}
class Port:
    def read(self,path,*,params):
        assert path=='/products/42'
        return Response()
assert WooCommerceProductReadAdapter(Port(),authorize=lambda p,q:True).get_product('42').id=='42'
"""
    result = subprocess.run([sys.executable,'-I','-c',code,installed],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
