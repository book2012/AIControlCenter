"""Replaceable, repository-only presentation mapping. Never commerce metadata.

Only completed SHOP_MEDIA_003_AGACHICHI assets are exposed. Planned records
intentionally resolve to the neutral image placeholder; Orange Coco sample
photos are inactive for the agachichi presentation.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "brands/agachichi/assets/media/SHOP_MEDIA_003.json"
UPLOAD_MANIFEST = ROOT / "brands/agachichi/assets/media/uploads/manifest.json"
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


@lru_cache(maxsize=1)
def _load_uploads(stamp: int) -> dict:
    payload = json.loads(UPLOAD_MANIFEST.read_text())
    if payload.get("schema_version") != 1 or payload.get("environment") != "DEV":
        raise ValueError("upload manifest invalid")
    result = {}
    root = (ROOT / "brands/agachichi/assets/media/uploads").resolve()
    for asset in payload.get("assets", []):
        category = str(asset["category"]).lower()
        identifier = str(asset["id"])
        if category not in CATEGORIES or not re.fullmatch(rf"ag-upload-{category}-[0-9]{{4}}", identifier):
            raise ValueError("upload media id invalid")
        path = f"brands/agachichi/assets/media/uploads/{identifier}.jpg"
        route = f"/homepage/assets/storefront/catalog/{category}/{identifier}.jpg"
        if asset.get("status") != "READY" or asset.get("target_path") != path or asset.get("photo_route") != route or asset.get("product_id") != identifier:
            raise ValueError("upload media binding invalid")
        target = (ROOT / path).resolve()
        if not target.is_relative_to(root) or not target.is_file() or target.is_symlink():
            raise ValueError("upload media path invalid")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != asset.get("sha256"):
            raise ValueError("upload media hash invalid")
        result[identifier] = {"path": target, "url": route, "category": category, "representative": True}
    return result


def assets() -> dict:
    try:
        result = dict(_load(MANIFEST.stat().st_mtime_ns))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return {}
    if UPLOAD_MANIFEST.is_file():
        try:
            result.update(_load_uploads(UPLOAD_MANIFEST.stat().st_mtime_ns))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            # A broken DEV upload must fail closed for that upload without
            # taking the validated base presentation media offline.
            pass
    return result


def photo(product: dict) -> str | None:
    if product.get("source") == "dev_upload":
        from core.homepage.storefront_gallery import front
        model = front(product["id"])
        if model is not None:return model["url"]
    asset = assets().get(product["id"])
    allowed_source = product["source"] == "demo" or product["source"] == "dev_upload"
    if allowed_source and asset and product["category"].lower() == asset["category"]:
        return asset["url"]
    return None


def browser_mapping() -> str:
    # A flat, validated ID-to-local-route map, not product data or model profiles.
    mapping={identifier: item["url"] for identifier, item in assets().items()}
    from core.homepage.storefront_gallery import assets as gallery_assets
    fronts={row["product_id"]:row["url"] for row in gallery_assets().values() if row["kind"]=="model-front"}
    for identifier in mapping:
        if identifier in fronts:mapping[identifier]=fronts[identifier]
    return json.dumps(mapping, separators=(",", ":"))
