"""Replaceable, repository-only presentation mapping. Never commerce metadata.

Only completed SHOP_MEDIA_003_AGACHICHI assets are exposed. Planned records
intentionally resolve to the neutral image placeholder; Orange Coco sample
photos are inactive for the agachichi presentation.
"""
from functools import lru_cache
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "brands/agachichi/assets/media/SHOP_MEDIA_003.json"
CATEGORIES = {"top": "women-tops", "bottom": "women-bottoms", "outer": "women-outer",
              "dress": "women-dresses", "bag": "women-bags", "acc": "women-accessories"}


@lru_cache(maxsize=1)
def _load(stamp: int) -> dict:
    assets = json.loads(MANIFEST.read_text())["assets"]
    result = {}
    for asset in assets:
        category = asset["category"].lower()
        identifier = asset["id"]
        if category not in CATEGORIES or not re.fullmatch(rf"oc-demo-{category}-[0-9]{{4}}", identifier):
            continue
        path = f"brands/agachichi/assets/media/catalog/{category}/{identifier}.jpg"
        route = f"/homepage/assets/storefront/catalog/{category}/{identifier}.jpg"
        if (asset["status"] != "GENERATED" or asset["target_path"] != path or asset["photo_route"] != route
                or asset["product_id"] != identifier or identifier in result):
            continue
        target = (ROOT / path).resolve()
        if target.is_relative_to((ROOT / "brands/agachichi/assets/media/catalog").resolve()) and target.is_file():
            result[identifier] = {"path": target, "url": route, "category": category,
                                  "representative": asset["homepage_representative"]}
    return result


def assets() -> dict:
    try:
        return _load(MANIFEST.stat().st_mtime_ns)
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def photo(product: dict) -> str | None:
    asset = assets().get(product["id"])
    if product["source"] == "demo" and asset and product["category"].lower() == asset["category"]:
        return asset["url"]
    return None


def browser_mapping() -> str:
    # A flat, validated ID-to-local-route map, not product data or model profiles.
    return json.dumps({identifier: item["url"] for identifier, item in assets().items()}, separators=(",", ":"))
