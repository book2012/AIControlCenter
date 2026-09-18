"""Read-only HTTP smoke check of the served dev preview, not just source files.

Usage: python3 scripts/check_orange_coco_preview.py [--origin URL]
Only the documented dev host or loopback origins are accepted. No redirects,
credentials, production endpoints, browser automation or writes are used.
"""
import argparse
import json
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERSION = "SHOP_MEDIA_003_AGACHICHI"
PATHS = [
    ("/homepage/storefront", 200),
    ("/homepage/storefront/search", 200),
    ("/homepage/storefront/search?category=women-tops&page=2", 200),
    ("/homepage/storefront/product/oc-demo-top-0001", 200),
    ("/homepage/storefront/product/no-such-product", 404),
    ("/homepage/assets/storefront/hero-boutique.jpg", 200),
    ("/shopping/products/oc-demo-top-0001", 200),
]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Unexpected preview redirect")


def check(origin: str) -> list[dict]:
    url = urlsplit(origin)
    if (url.username or url.password or url.path not in ("", "/") or url.query or url.fragment
            or not (url.scheme == "http" and url.hostname == "127.0.0.1" and url.port in (18080, 18081)
                    or url.scheme == "https" and url.hostname == "dev.bokstory.duckdns.org" and url.port in (None, 443))):
        raise ValueError("Use the documented dev preview or loopback port 18080/18081")
    opener, results = build_opener(NoRedirect), []
    for path, expected in PATHS:
        try:
            response = opener.open(Request(origin.rstrip("/") + path, method="GET"), timeout=10)
        except HTTPError as error:
            response = error
        with response:
            body = response.read(2_000_001)
            assert len(body) <= 2_000_000, "Unexpected preview response size"
            assert response.status == expected, f"Unexpected HTTP status for {path}: expected {expected}, received {response.status}"
            assert response.headers.get("X-Shop-Presentation") == VERSION, "Stale or incorrect preview composition"
            media = response.headers.get("Content-Type", "")
            if "text/html" in media:
                text = body.decode("utf-8")
                assert "{{" not in text and "}}" not in text, "Unrendered template served"
                assert 'lang="ko"' in text and "현재 구매는 지원하지 않습니다." in text
                if path == "/homepage/storefront":
                    assert 'href="/homepage/storefront?category=women-tops"' in text
                    # Home intentionally renders only the bounded first feed page;
                    # the feed count/load-more affordance proves the full catalog remains available.
                    assert len(re.findall(r'data-product-id="[^"]+"', text)) == 24
                    assert 'id="feed-load-more"' in text and 'data-page="2"' in text
                    assert 'id="feed-count">상품 120개' in text
                    assert all(f'data-feed-filter="{filter_name}"' in text
                               for filter_name in ("all", "hot", "sale", "update", "top", "bottom", "outer", "dress", "bag", "acc"))
                    assert "<form" not in text
                if path == "/homepage/storefront/search":
                    assert len(re.findall(r'data-product-id="[^"]+"', text)) == 12
            elif "image/jpeg" in media:
                assert body.startswith(b"\xff\xd8\xff")
            elif path.startswith("/shopping/products/"):
                product = json.loads(body)
                assert product["id"] == "oc-demo-top-0001" and product["source"] == "demo"
                assert isinstance(product["price"], str)
            else:
                raise AssertionError("Unexpected response media type")
            results.append({"path": path, "status": response.status, "presentation": VERSION})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    print(json.dumps({"origin": args.origin, "checks": check(args.origin), "result": "PASS"}, ensure_ascii=False, indent=2))
