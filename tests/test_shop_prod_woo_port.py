from types import SimpleNamespace
from decimal import Decimal
import pytest
from ops.macos.shopping import prod_woo_port as port
from test_shop_guest_checkout import LiveCatalog
from core.shopping.order_core.guest_chat import GuestCart

def test_order_port_rejects_other_host_path_and_credentials_before_provider(monkeypatch):
    calls=[];monkeypatch.setattr(port,'rest',lambda *args:calls.append(args))
    session=port.ProductionOrderSession(checkout=None,credentials=('private-a','private-b'))
    for url in ['https://dev.bokstory.duckdns.org/wp-json/wc/v3/orders','http://bokstory.duckdns.org/wp-json/wc/v3/orders','https://bokstory.duckdns.org/wp-json/wc/v3/products/10','https://bokstory.duckdns.org/wp-json/wc/v3/orders?x=1']:
        with pytest.raises(ValueError):session.get(url,auth=('private-a','private-b'))
    with pytest.raises(ValueError):session.get('https://bokstory.duckdns.org/wp-json/wc/v3/orders/1',auth=('wrong','wrong'))
    assert not calls

def test_production_quote_revalidates_stock_and_explicit_policy():
    cart=GuestCart.model_validate({'line_items':[{'product_id':'10','variation_id':'11','quantity':2}]})
    quote=port.production_quote(LiveCatalog(),cart)
    assert quote['final_total']=='58000' and quote['shipping_policy']=='PROD_INCLUDED_SHIPPING'
    class SoldOut(LiveCatalog):
        def read(self,path):return [{**super().read(path)[0],'stock_quantity':1}]
    with pytest.raises(ValueError):port.production_quote(SoldOut(),cart)

@pytest.mark.parametrize('field,value',[('shipping_total','100'),('total','1'),('currency','USD'),('customer_id',99)])
def test_production_order_receipt_must_bind_delivery_total_and_customer(monkeypatch,field,value):
    draft={'state':'CONFIRMED','digest':'d'*64,'body':{'billing':{'phone':'+821012345678'},'shipping':{'address_1':'private address'},'line_items':[{'product_id':'10','variation_id':'11','quantity':1}],'quote':{'final_total':'29000'}}}
    payload={'customer_id':7,'line_items':[{'product_id':10,'variation_id':11,'quantity':1}],'meta_data':[{'key':'_aicc_order_operation','value':'t'}]}
    raw={**payload,'billing':draft['body']['billing'],'shipping':draft['body']['shipping'],'total':'29000','shipping_total':'0','total_tax':'0','currency':'KRW','meta_data':[{'key':'_aicc_delivery_digest','value':draft['digest']}]}
    raw[field]=value;monkeypatch.setattr(port,'rest',lambda *args:{'status':201,'body':raw})
    session=port.ProductionOrderSession(checkout=SimpleNamespace(by_provider_tag=lambda *a,**kw:draft),credentials=('a','b'))
    if field=='customer_id':
        # The governed Woo writer also validates provider customer; port checks early.
        with pytest.raises(ValueError):session.post('https://bokstory.duckdns.org/wp-json/wc/v3/orders',auth=('a','b'),json=payload)
    else:
        with pytest.raises(ValueError):session.post('https://bokstory.duckdns.org/wp-json/wc/v3/orders',auth=('a','b'),json=payload)
