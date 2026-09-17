"""Export real canonical TestClient responses for SHOP_UI_002 offline browser QA.

Usage: .venv/bin/python -B tests/shop_ui_001_fixtures.py /private/tmp/shop-ui-002.json
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from urllib.parse import urlencode
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
for key in tuple(os.environ):
    if key not in {"PATH", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT"}:
        del os.environ[key]
sys.dont_write_bytecode = True

from core.config.loader import ConfigLoader

ConfigLoader.load = lambda self: {"exists": False, "loaded": False}


def denied(*args, **kwargs):
    raise AssertionError("SHOP_UI_001 fixture export: external operation blocked")


socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
subprocess.Popen = denied

from test_shop_ui_001_storefront import fixture_client

class ProductLinks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("class") == "product-link" and attrs.get("href"):
            self.links.append(attrs["href"])


responses = {}
with fixture_client() as client:
    products = client.get("/shopping/products?page=1&page_size=100").json()["items"]
    categories = client.get("/shopping/categories").json()["items"]
    paths = ["/homepage/storefront", "/homepage/storefront/search", "/homepage/assets/storefront.css", "/homepage/assets/storefront.js", "/shopping/categories"]
    for product in products:
        paths.extend((f"/homepage/storefront/product/{product['id']}", f"/shopping/products/{product['id']}"))
    paths.extend(("/homepage/storefront/product/no-such-product", "/shopping/products/no-such-product"))
    queries = [{}, *({"category": category["id"]} for category in categories),
               *({"q": query} for query in ("미니멀", "내추럴", "주말", "출근", "블라우스", "no-such-coco-piece")),
               {"category": "women-tops", "q": "블라우스"},
               {"category": "women-tops", "q": "미니멀"}]
    for query in queries:
        endpoint = "/shopping/search" if query else "/shopping/products"
        first = client.get(endpoint, params={"page": 1, "page_size": 12, **query}).json()
        for page in range(1, max(1, (first["total"] + 11) // 12) + 1):
            paths.append(f"{endpoint}?{urlencode({'page': page, 'page_size': 12, **query})}")
            browse = {**query, **({"page": page} if page > 1 else {})}
            paths.append("/homepage/storefront/search" + ("?" + urlencode(browse) if browse else ""))
    for category in ("new", "best"):
        paths.append(f"/shopping/search?category={category}&page=1&page_size=100")
        paths.append(f"/shopping/search?category={category}&page=1&page_size=4")
    paths.extend((
        "/homepage/storefront?category=women-tops&q=블라우스&page=1",
        "/homepage/storefront/product/oc-demo-top-0001?" + urlencode({"return_to": "/homepage/storefront?category=women-tops&page=2"}),
        "/homepage/storefront/product/no-such-product?" + urlencode({"return_to": "https://untrusted.invalid/"}),
    ))
    for path in paths:
        if path in responses:
            continue
        response = client.get(path, follow_redirects=False)
        expected = 404 if "no-such-product" in path else 307 if path.startswith("/homepage/storefront?") else 200
        assert response.status_code == expected, path
        responses[path] = {"status": response.status_code, "contentType": response.headers.get("content-type", "text/html"), "body": response.text}
        if response.status_code == 307:
            responses[path]["headers"] = {"location": response.headers["location"]}
        if response.headers.get("content-type", "").startswith("text/html"):
            assert "{{" not in response.text and "}}" not in response.text, path
            assert response.headers["x-shop-presentation"] in {"SHOP_UI_002_SSR_MEDIA_001", "SHOP_MEDIA_002_CATEGORY_LOOKBOOK"}
            paths.extend(ProductLinks(response.text).links)

Path(sys.argv[1]).write_text(json.dumps(responses, ensure_ascii=False), encoding="utf-8")
print(f"Exported {len(responses)} canonical/static fixture responses; no runtime or network.")
