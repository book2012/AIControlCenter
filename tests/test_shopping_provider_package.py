"""Installed-wheel boundaries using synthetic vendor data only."""
import asyncio
from pathlib import Path
import subprocess
import sys
import pytest
pytest.importorskip("aicc_plugin_shopping")
from aicc_plugin_shopping.adapters.woocommerce_extended_read import WooCommerceCatalogReadAdapter, WooCommerceOrderReadAdapter
from aicc_plugin_shopping.adapters.woocommerce_product_read import WooCommerceAPIError
from aicc_plugin_shopping.adapters.woocommerce_normalization import build_woocommerce_commerce_read_adapter
from aicc_plugin_shopping.adapters.woocommerce_commerce_read import WooCommerceCommerceReadError
from test_woocommerce_plugin_read import Port, Response, PRODUCT
from test_shopping_woocommerce_normalization import FakeVendor


def test_category_and_search_use_explicit_scoped_port():
    port = Port(Response([{"id": 2, "name": "Fixture", "slug": "fixture", "count": 1}]), Response([PRODUCT]))
    approvals = []
    def approve(path, query):
        approvals.append((path, dict(query)))
        query.clear()
        return True
    adapter = WooCommerceCatalogReadAdapter(port, authorize=approve)
    assert adapter.list_categories()[0]["id"] == "2"
    values, total = adapter.search_products(query="fixture", category="2", minimum_price=1,
        maximum_price=30, in_stock=True, page=1, page_size=10)
    assert values[0].id == "42" and total == 1
    assert len(port.calls) == len(approvals) == 2
    assert port.calls[0][0] == "/products/categories"
    assert port.calls[1][1]["status"] == "publish"
    assert port.calls[1][1]["stock_status"] == "instock"


@pytest.mark.parametrize("approved", [False, None, 1, "yes"])
@pytest.mark.parametrize("kind", ["categories", "order"])
def test_extended_reads_deny_without_exact_true(approved, kind):
    port = Port()
    if kind == "categories":
        operation = WooCommerceCatalogReadAdapter(port, authorize=lambda p,q: approved).list_categories
    else:
        adapter = WooCommerceOrderReadAdapter(port, authorize=lambda p,q: approved)
        operation = lambda: adapter.get_order_summary_raw("7")
    with pytest.raises(WooCommerceAPIError):
        operation()
    assert port.calls == []


@pytest.mark.parametrize("identifier", ["", "0", "07", "../products/42", "7?x", "７", "1"*21])
def test_order_scope_rejects_noncanonical_identifiers_before_port(identifier):
    port = Port()
    approvals = []
    adapter = WooCommerceOrderReadAdapter(port, authorize=lambda p,q: approvals.append(p))
    with pytest.raises(WooCommerceAPIError):
        adapter.get_order_summary_raw(identifier)
    assert port.calls == [] and approvals == []


def test_order_not_found_is_structured_and_non404_errors_are_sanitized():
    port = Port(Response({},status=404), RuntimeError("fixture-private"), Response({"id":7}))
    adapter = WooCommerceOrderReadAdapter(port, authorize=lambda p,q: True)
    assert adapter.get_order_summary_raw("7") is None
    with pytest.raises(WooCommerceAPIError) as error:
        adapter.get_order_summary_raw("7")
    assert "fixture-private" not in str(error.value) and error.value.__context__ is None
    assert adapter.get_order_summary_raw("7") == {"id":7}
    assert all(call == ("/orders/7", {"context":"view"}) for call in port.calls)


@pytest.mark.parametrize("approved", [False, None, 1])
def test_canonical_read_denial_precedes_vendor_access(approved):
    vendor = FakeVendor()
    adapter = build_woocommerce_commerce_read_adapter(vendor=vendor, currency_code="KRW", currency_minor_unit=0,
        authorize=lambda **kwargs: approved, validate=lambda schema,value: True)
    with pytest.raises(WooCommerceCommerceReadError) as error:
        asyncio.run(adapter.get_order_summary(context={},order_id="7"))
    assert error.value.reason_code == "external_read_policy_denied" and vendor.calls == []


@pytest.mark.parametrize("validated", [False, None, 1])
def test_canonical_schema_validator_requires_exact_true(validated):
    adapter = build_woocommerce_commerce_read_adapter(vendor=FakeVendor(),currency_code="KRW",currency_minor_unit=0,
        authorize=lambda **kwargs: True, validate=lambda schema,value: validated)
    with pytest.raises(WooCommerceCommerceReadError) as error:
        asyncio.run(adapter.get_product(context={},product_id="42"))
    assert error.value.reason_code == "normalization_error"


def test_installed_provider_and_storage_import_without_host_or_transport(tmp_path):
    import aicc_plugin_shopping
    installed = str(Path(aicc_plugin_shopping.__file__).resolve().parent.parent)
    code = r"""
import sys,builtins,asyncio
sys.path.insert(0,sys.argv[1])
original=builtins.__import__
def guard(name,*args,**kwargs):
    if kwargs.get('level',args[3] if len(args)>3 else 0)==0 and name.split('.')[0] in {'core','ops','integrations','requests','fastapi'}:
        raise AssertionError('unexpected dependency: '+name)
    return original(name,*args,**kwargs)
builtins.__import__=guard
from aicc_plugin_shopping.storage_resource import ShoppingStorageResource
from aicc_plugin_shopping import customer_auth,customer_identity,customer_sessions,migration_contract
from aicc_plugin_shopping.adapters.woocommerce_normalization import build_woocommerce_commerce_read_adapter
class Vendor:
    def get_order_summary_raw(self,identifier):
        return {'id':7,'status':'processing','currency':'KRW','total':'19','customer_id':999,
          'date_created_gmt':'2026-07-27T02:00:00','date_modified_gmt':'2026-07-27T03:00:00','line_items':[{'quantity':1}]}
seen=[]
a=build_woocommerce_commerce_read_adapter(vendor=Vendor(),currency_code='KRW',currency_minor_unit=0,
    authorize=lambda **kwargs:True,validate=lambda schema,value:seen.append(schema) or True)
value=asyncio.run(a.get_order_summary(context={},order_id='7'))
assert value['total']=={'amount_minor':19,'currency':'KRW'} and 'customer_id' not in value
assert seen
resource=ShoppingStorageResource(sys.argv[2]+'/missing.db',data_root=sys.argv[2])
assert not resource.ready
"""
    result = subprocess.run([sys.executable,"-I","-c",code,installed,str(tmp_path)],capture_output=True,text=True)
    assert result.returncode == 0,result.stderr
    assert list(tmp_path.iterdir()) == []
    package = Path(aicc_plugin_shopping.__file__).parent
    for source in package.rglob("*.py"):
        assert "pf.kakao.com" not in source.read_text()
        assert "open.kakao.com" not in source.read_text()
