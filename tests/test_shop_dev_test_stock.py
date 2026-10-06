import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.homepage.dev_test_stock import overlay,PATH
from core.shopping.order_core.guest_chat import GuestShoppingChat
from test_shop_guest_chat import Catalog

def test_test_stock_covers_60_combinations_and_preserves_confirmed_coats():
    with TestClient(create_app()) as client:
        rows=client.get('/shopping/products?page_size=100').json()['items']
        combined=[r for r in rows if r['variants'][0]['option_type']=='color_size']
        assert len(combined)==17 and sum(len(r['variants']) for r in combined)==60
        for row in combined:
            assert row['in_stock'] and all(v['available'] for v in row['variants'])
            assert all(' / ' in v['label'] for v in row['variants'])
            page=client.get('/homepage/storefront/product/'+row['id']).text
            assert 'data-combined="true"' in page and 'DEV 테스트 재고' in page
        assert len(next(r for r in rows if r['id']=='ag-upload-outer-0001')['variants'])==3
        assert len(next(r for r in rows if r['id']=='ag-upload-outer-0002')['variants'])==2

@pytest.mark.parametrize('change',['environment','quantity','scope','sizes','hash'])
def test_test_overlay_rejects_invalid_or_production_data(tmp_path,change):
    source=PATH.with_name('dev-upload-products.json')
    records=json.loads(source.read_text())['products'];data=json.loads(PATH.read_text())
    pid=next(iter(data['products']))
    if change=='environment':data['environment']='PROD'
    if change=='quantity':data['products'][pid]['quantity_per_combination']=99
    if change=='scope':data['products']['ag-upload-outer-0001']=data['products'][pid]
    if change=='sizes':data['products'][pid]['sizes']=['XL']
    if change=='hash':data['catalog_sha256']='0'*64
    path=tmp_path/'stock.json';path.write_text(json.dumps(data))
    with pytest.raises(ValueError):overlay(records,source,path)

def test_quote_rejects_more_than_available_quantity():
    class Limited(Catalog):
        def available_quantity(self,pid,vid):return 3
    chat=GuestShoppingChat(Limited())
    base={'product_id':'10','variation_id':'11'}
    assert chat.quote({'line_items':[{**base,'quantity':3}]})['order_created'] is False
    with pytest.raises(ValueError,match='INSUFFICIENT_STOCK'):chat.quote({'line_items':[{**base,'quantity':4}]})
