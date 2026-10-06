"""Reviewed photo metadata, option boundaries and option-adjacent cart presentation."""
from pathlib import Path
import copy,json,hashlib
import pytest
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.homepage import storefront_gallery
from core.shopping.adapters.demo_commerce import DemoCommerceCatalogAdapter
from core.shopping.order_core.guest_chat import GuestShoppingChat,GuestQuestion,GuestCart
from test_shop_guest_chat import Catalog
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'brands/agachichi/catalog/dev-upload-products.json'
def batch():return [v for v in json.loads(PATH.read_text())['products'] if v.get('inventory_pending') is True]
def test_photo_batch_identity_prices_colors_and_no_fabricated_stock():
    rows=batch();assert len(rows)==17
    sources=[name for row in rows for name in row['source_files']]
    assert len(sources)==len(set(sources))==18
    assert next(v for v in rows if v['id']=='ag-upload-outer-0004')['source_files']==['70626.jpg','70624.jpg']
    assert all(v['price']>0 and v['price_basis']=='user_authorized_temporary' and not any(v['inventory'].values()) for v in rows)
    adapter=DemoCommerceCatalogAdapter(upload_overlay=PATH,include_samples=False)
    for row in rows:
        p=adapter.get_product(row['id']);assert not p.in_stock
        assert [(v.label,v.option_type,v.available) for v in p.variants]==[(v['label'],'color',False) for v in row['color_options']]
    assert [v.label for v in adapter.get_product('ag-upload-top-0006').variants]==['그레이','아이보리','브라운','네이비','블랙']
    assert [v.label for v in adapter.get_product('ag-upload-top-0005').variants]==['스카이블루','네이비']
    assert adapter.get_product('ag-upload-outer-0001').in_stock
@pytest.mark.parametrize('change',['positive_stock','bad_color_id','duplicate','missing_inventory','wrong_pending_type'])
def test_color_and_unconfirmed_inventory_fail_closed(tmp_path,change):
    row=copy.deepcopy(batch()[0])
    if change=='positive_stock':row['inventory'][next(iter(row['inventory']))]=1
    if change=='bad_color_id':row['color_options'][0]['id']='../unsafe'
    if change=='duplicate':row['color_options'].append(dict(row['color_options'][0]))
    if change=='missing_inventory':row['inventory']={'wrong':0}
    if change=='wrong_pending_type':row['inventory_pending']='true'
    path=tmp_path/'catalog.json';path.write_text(json.dumps({'schema_version':1,'environment':'DEV','products':[row]}))
    with pytest.raises(ValueError):DemoCommerceCatalogAdapter(upload_overlay=path,include_samples=False)
def test_all_uploaded_media_and_detail_order_are_bound():
    assets=storefront_gallery.assets()
    with TestClient(create_app()) as c:
        for row in batch():
            pid=row['id'];html=c.get('/homepage/storefront/product/'+pid).text
            assert 'COLOR' in html and '사이즈·재고 확인 중' in html
            assert html.index('id="variant-section"')<html.index('id="commerce-panel"')<html.index('id="description-section"')
            assert pid+'-original.jpg' not in html
            assert html.index(pid+'-garment-cutout.webp')<html.index(pid+'-model-other.jpg')
            for kind,ext in [('model-front','jpg'),('garment-cutout','webp'),('model-other','jpg')]:
                asset=assets[pid+'-'+kind+'.'+ext]
                assert hashlib.sha256(asset['path'].read_bytes()).hexdigest()==asset['sha256']
                assert c.get(asset['url']).status_code==200
        cart=c.get('/homepage/storefront/cart')
        assert cart.status_code==200 and 'data-cart-page="true"' in cart.text
        assert cart.text.count('id="shop-chat"')==1 and 'storefront-commerce.js' in cart.text
class Pending(Catalog):
    def inventory_pending(self,key):return True
    def temporary_price(self,key):return True
    def get_product(self,key):return {**super().get_product(key),'in_stock':False}
def test_pending_chat_does_not_claim_stock_or_sale_price():
    chat=GuestShoppingChat(Pending())
    stock=chat.answer(GuestQuestion(product_id='10',message='재고 있나요'))
    assert '확인 중' in stock['message'] and '품절' not in stock['message']
    assert '임시 가격' in chat.answer(GuestQuestion(product_id='10',message='가격'))['message']
    purchase=chat.answer(GuestQuestion(product_id='10',message='주문'))
    assert purchase['action']=='ANSWER' and '주문할 수 없습니다' in purchase['message']
    with pytest.raises(ValueError):chat.quote(GuestCart.model_validate({'line_items':[{'product_id':'10','variation_id':'11','quantity':1}]}))

def test_dev_provider_color_price_and_pending_boundary():
    from ops.macos.shopping.dev_order_runtime import DevCatalog
    class Provider(DevCatalog):
        def read(self,path):
            if "/variations" in path:return [dict(id=2,attributes=[{"option":"그레이"}],price="69000",status="publish",stock_status="instock",manage_stock=True,stock_quantity=99)]
            return dict(id=1,sku="aicc-dev-test",name="니트",slug="knit",description="",price="",stock_status="instock")
    catalog=Provider({},{"active_products":[dict(product_id=1,demo_id="ag-upload-top-0006",sku="aicc-dev-test",category="TOP",option_type="color",inventory_pending=True)]})
    p=catalog.get_product("1")
    assert p["price"]=="69000" and not p["in_stock"]
    assert p["variants"][0].option_type=="color" and not p["variants"][0].available
    assert "확인 중" in catalog.stock_summary("1")
    with pytest.raises(ValueError):catalog.get_product("other")
