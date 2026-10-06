import pytest
from fastapi.testclient import TestClient
from core.homepage.preview import create_app

@pytest.mark.parametrize("path",["/homepage/storefront","/homepage/storefront?collection=hot","/homepage/storefront?collection=update","/homepage/storefront/search","/homepage/storefront/search?category=women-outer"])
def test_customer_pages_have_uploads_and_no_sample_selection(path):
    with TestClient(create_app()) as c:
        r=c.get(path)
        assert r.status_code==200
        assert "ag-upload-outer-0001" in r.text and "ag-upload-outer-0002" in r.text
        assert "oc-demo-" not in r.text


def test_upload_catalog_counts_pagination_and_direct_sample_lookup():
    with TestClient(create_app()) as c:
        rows=c.get("/shopping/products?page_size=1").json()
        assert rows["total"]==2 and len(rows["items"])==1
        assert c.get("/shopping/products?page=3&page_size=1").json()["items"]==[]
        categories=c.get("/shopping/categories").json()["items"]
        assert all(row["count"]==2 for row in categories)
        assert c.get("/shopping/products/oc-demo-top-0001").status_code==404
        assert c.get("/homepage/storefront/product/oc-demo-top-0001").status_code==404
        assert "oc-demo-" not in c.get("/homepage/storefront?category=women-tops").text
        assert "상품 0개" in c.get("/homepage/storefront/search?q=소프트+린넨").text
        assert "상품 2개" in c.get("/homepage/storefront/search").text


def test_explicit_sample_fixture_remains_available():
    with TestClient(create_app(include_samples=True)) as c:
        assert c.get("/shopping/products").json()["total"]==122
        assert c.get("/homepage/storefront/product/oc-demo-top-0001").status_code==200
