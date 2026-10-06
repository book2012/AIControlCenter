"""Color previews remain independent of the stock-gated purchase selection."""
import json,copy
import pytest
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.homepage import storefront_gallery as gallery

@pytest.mark.parametrize("pid,count",[("ag-upload-top-0005",2),("ag-upload-top-0006",5)])
def test_each_color_has_a_manifest_bound_photo(pid,count):
    rows=gallery.color_fronts(pid)
    assert len(rows)==count
    assert len({v["url"] for v in rows.values()})==count
    with TestClient(create_app(test_inventory=False)) as client:
        html=client.get("/homepage/storefront/product/"+pid).text
        assert 'id="purchase-controls"' in html
        assert 'id="purchase-color"' in html and 'id="purchase-size"' in html
        assert 'id="purchase-quantity"' in html and '사이즈 확인 중' in html
        for color,row in rows.items():
            assert 'data-color-id="'+color+'"' in html
            assert row["url"] in html
            assert client.get(row["url"]).status_code==200

def test_existing_size_products_also_show_color_and_quantity():
    with TestClient(create_app(test_inventory=False)) as client:
        for pid,label in [("ag-upload-outer-0001","카멜"),("ag-upload-outer-0002","오트밀")]:
            text=client.get("/homepage/storefront/product/"+pid).text
            assert 'id="purchase-color"' in text and label in text
            assert 'id="purchase-size"' in text and 'id="purchase-quantity"' in text
            assert '>M</button>' in text and 'data-variant-id=' in text

@pytest.mark.parametrize("bad",["../navy","missing","gray"])
def test_gallery_rejects_unbound_color(tmp_path,monkeypatch,bad):
    payload=json.loads(gallery.MANIFEST.read_text())
    row=next(v for v in payload["assets"] if v["product_id"]=="ag-upload-top-0005" and v["kind"]=="color-front")
    row["color_id"]=bad
    path=tmp_path/"gallery.json";path.write_text(json.dumps(payload))
    monkeypatch.setattr(gallery,"MANIFEST",path)
    assert gallery.assets()=={}


def test_single_color_preview_keeps_its_existing_front_visible():
    catalog=json.loads((gallery.ROOT/'brands/agachichi/catalog/dev-upload-products.json').read_text())['products']
    for row in catalog:
        if len(row.get('color_options',[]))==1:
            color=row['color_options'][0]['id']
            preview=gallery.color_fronts(row['id'])[color]
            assert preview['url'].endswith(row['id']+'-model-front.jpg')
