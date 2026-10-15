import pytest
from fastapi.testclient import TestClient
from core.homepage.preview import create_app

@pytest.mark.parametrize("path",["/homepage/storefront","/homepage/storefront?collection=hot","/homepage/storefront?collection=update","/homepage/storefront/search","/homepage/storefront/search?category=women-outer"])
def test_customer_pages_have_uploads_and_no_sample_selection(path):
    with TestClient(create_app(managed_projection=False)) as c:
        r=c.get(path)
        assert r.status_code==200
        assert "ag-upload-outer-0001" in r.text and "ag-upload-outer-0002" in r.text
        assert "oc-demo-" not in r.text


def test_upload_catalog_counts_pagination_and_direct_sample_lookup():
    with TestClient(create_app(managed_projection=False)) as c:
        rows=c.get("/shopping/products?page_size=1").json()
        assert rows["total"]==21 and len(rows["items"])==1
        all_products=c.get("/shopping/products?page_size=100").json()["items"]
        assert any(row["id"]=="ag-upload-bottom-0002" for row in all_products)
        assert c.get("/shopping/products?page=22&page_size=1").json()["items"]==[]
        target=c.get("/shopping/products/ag-upload-bottom-0002").json()
        assert target["name"]=="베이지 플라워 레이스 롱 스커트" and target["price"]=="79000"
        assert target["in_stock"] is False and target["variants"][0]["available"] is False
        detail=c.get("/homepage/storefront/product/ag-upload-bottom-0002")
        assert detail.status_code==200 and "사이즈·재고 확인 중" in detail.text
        assert 'data-demo-product="ag-upload-bottom-0002"' in detail.text
        assert "DEV 주문 테스트 · 실제 결제·배송 없음" in detail.text
        categories=c.get("/shopping/categories").json()["items"]
        assert {row["id"]:row["count"] for row in categories}=={"new":21,"women-tops":6,"women-dresses":4,"women-bottoms":2,"women-outer":6,"women-bags":2,"women-accessories":1}
        assert c.get("/shopping/products/oc-demo-top-0001").status_code==404
        assert c.get("/homepage/storefront/product/oc-demo-top-0001").status_code==404
        assert "oc-demo-" not in c.get("/homepage/storefront?category=women-tops").text
        assert "상품 0개" in c.get("/homepage/storefront/search?q=소프트+린넨").text
        assert "상품 21개" in c.get("/homepage/storefront/search").text


def test_explicit_sample_fixture_remains_available():
    with TestClient(create_app(include_samples=True,managed_projection=False)) as c:
        assert c.get("/shopping/products").json()["total"]==141
        assert c.get("/homepage/storefront/product/oc-demo-top-0001").status_code==200
