from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from ops.macos.shopping.dev_second_coat_register import read_spec
from core.homepage import storefront_media
def test_second_coat_reviewed_commerce_media_and_tags():
    spec,image,digest=read_spec()
    assert spec["price"]==450000 and spec["inventory"]=={"M":1,"L":1}
    assert image.is_file() and len(digest)==64
    assert "울" not in spec["description"] and "캐시미어" not in spec["description"]
    assert storefront_media.assets()[spec["id"]]["path"]==image
    with TestClient(create_app()) as c:
        r=c.get("/homepage/storefront/product/"+spec["id"])
        assert r.status_code==200 and "450,000원" in r.text
        assert "#오트밀베이지" in c.get("/homepage/storefront").text and 'id="commerce-panel"' in r.text
def test_dev_home_hot_is_explicit_editorial_and_default_update():
    with TestClient(create_app()) as c:
        home=c.get("/homepage/storefront")
        assert home.status_code==200 and 'id="featured-hot-title">HOT' in home.text
        assert 'id="feed-title">UPDATE' in home.text and "에디터가 고른" in home.text
        assert "ag-upload-outer-0002" in home.text and "ag-upload-outer-0001" in home.text
        hot=c.get("/homepage/storefront?collection=hot")
        assert hot.status_code==200 and "HOT 상품이 없습니다" not in hot.text
        assert "ag-upload-outer-0002" in hot.text
        search=c.get("/homepage/storefront/search")
        assert search.status_code==200 and "상품 19개" in search.text
        assert c.get("/homepage/storefront/product/no-such-product").status_code==404
