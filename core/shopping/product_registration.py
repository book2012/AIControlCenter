"""Pure validation for the isolated DEV single-product registration workflow."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PRODUCT_ID = re.compile(r"^ag-upload-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$")
OPTION_ID = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
SIZE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .-]{0,15}$")
GALLERY_KINDS = {"original", "model-angles", "model-front", "model-other", "garment-cutout", "color-front"}
REQUIRED_GALLERY_KINDS = {"original", "model-front", "garment-cutout", "model-other"}
CATEGORY_LABELS = {
    "top": "TOP", "bottom": "BOTTOM", "outer": "OUTER", "dress": "DRESS",
    "bag": "BAG", "acc": "ACC",
}


def _fail(code: str) -> None:
    raise ValueError(code)


def _read_json(path: Path, code: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail(code)
    if not isinstance(value, dict):
        _fail(code)
    return value


def _verified_file(repo: Path, root: Path, relative: str, expected_sha: str, code: str) -> Path:
    if not isinstance(relative, str) or not relative:
        _fail(code)
    raw = repo / relative
    try:
        if raw.is_symlink() or not raw.is_file():
            _fail(code)
        resolved = raw.resolve(strict=True)
        resolved_root = root.resolve(strict=True)
        if not resolved.is_relative_to(resolved_root) or raw.absolute() != resolved:
            _fail(code)
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError:
        _fail(code)
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or digest != expected_sha:
        _fail(code)
    return resolved


def _option_rows(spec: dict) -> list[dict]:
    option_type = spec.get("option_type", "size")
    inventory = spec.get("inventory")
    if not isinstance(inventory, dict) or not inventory:
        _fail("PRODUCT_INVENTORY_INVALID")
    for quantity in inventory.values():
        if type(quantity) is not int or quantity < 0 or quantity > 9999:
            _fail("PRODUCT_INVENTORY_INVALID")
    if spec.get("inventory_pending") is True and any(inventory.values()):
        _fail("PENDING_INVENTORY_MUST_BE_ZERO")
    if type(spec.get("inventory_pending")) is not bool:
        _fail("PRODUCT_INVENTORY_STATE_INVALID")

    colors = spec.get("color_options") or []
    if not isinstance(colors, list):
        _fail("PRODUCT_OPTIONS_INVALID")
    color_by_id = {}
    for color in colors:
        if not isinstance(color, dict):
            _fail("PRODUCT_OPTIONS_INVALID")
        color_id, label = color.get("id"), color.get("label")
        if (not isinstance(color_id, str) or not OPTION_ID.fullmatch(color_id)
                or not isinstance(label, str) or not label.strip()
                or color_id in color_by_id or label in color_by_id.values()):
            _fail("PRODUCT_OPTIONS_INVALID")
        color_by_id[color_id] = label

    sizes = spec.get("size_options")
    if sizes is None:
        sizes = list(inventory) if option_type == "size" else []
    if not isinstance(sizes, list):
        _fail("PRODUCT_OPTIONS_INVALID")
    if any(not isinstance(size, str) or not SIZE_LABEL.fullmatch(size) for size in sizes):
        _fail("PRODUCT_OPTIONS_INVALID")
    if len(set(sizes)) != len(sizes):
        _fail("PRODUCT_OPTIONS_INVALID")

    expected = set()
    if option_type == "color":
        if not color_by_id:
            _fail("PRODUCT_OPTIONS_INVALID")
        expected = set(color_by_id)
    elif option_type == "size":
        if not sizes:
            _fail("PRODUCT_OPTIONS_INVALID")
        expected = set(sizes)
    elif option_type == "color_size":
        if not color_by_id or not sizes:
            _fail("PRODUCT_OPTIONS_INVALID")
        expected = {f"{color}--{size.lower()}" for color in color_by_id for size in sizes}
    else:
        _fail("PRODUCT_OPTION_TYPE_INVALID")
    if set(inventory) != expected:
        _fail("PRODUCT_INVENTORY_OPTION_MISMATCH")

    result = []
    for key in sorted(expected):
        if option_type == "color":
            attrs = {"color": color_by_id[key]}
            label = color_by_id[key]
        elif option_type == "size":
            attrs = {"size": key.upper()}
            label = key.upper()
        else:
            color, size = key.split("--", 1)
            attrs = {"color": color_by_id[color], "size": size.upper()}
            label = f"{color_by_id[color]} / {size.upper()}"
        result.append({"key": key, "label": label, "attributes": attrs, "stock": inventory[key]})
    return result


def validate_registration(repo: Path, catalog_id: str) -> dict:
    """Load a DEV upload, verify option/media bindings, return safe Woo payload."""
    repo = Path(repo).resolve()
    if not isinstance(catalog_id, str) or not PRODUCT_ID.fullmatch(catalog_id):
        _fail("PRODUCT_ID_INVALID")
    catalog_path = repo / "brands/agachichi/catalog/dev-upload-products.json"
    catalog = _read_json(catalog_path, "DEV_CATALOG_INVALID")
    if catalog.get("environment") != "DEV" or catalog.get("schema_version") != 1:
        _fail("DEV_CATALOG_REQUIRED")
    rows = catalog.get("products")
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == catalog_id] if isinstance(rows, list) else []
    if len(matches) != 1:
        _fail("PRODUCT_ID_NOT_UNIQUE")
    spec = matches[0]

    if (spec.get("source") != "user_upload" or spec.get("enabled") is not True
            or not isinstance(spec.get("name"), str) or not spec["name"].strip()
            or len(spec["name"]) > 200 or not isinstance(spec.get("description"), str)
            or not spec["description"].strip() or len(spec["description"]) > 20000):
        _fail("PRODUCT_CONTENT_INVALID")
    category = spec.get("category")
    if not isinstance(category, str) or category not in CATEGORY_LABELS or catalog_id.split("-")[2] != category:
        _fail("PRODUCT_CATEGORY_INVALID")
    price = spec.get("price")
    if spec.get("price_status") != "READY" or type(price) is not int or price < 1 or price > 10000000:
        _fail("PRODUCT_PRICE_NOT_READY")
    sale = spec.get("sale_price")
    if sale is not None and (type(sale) is not int or sale < 1 or sale >= price):
        _fail("PRODUCT_SALE_PRICE_INVALID")
    if spec.get("currency", "KRW") != "KRW":
        _fail("PRODUCT_CURRENCY_INVALID")
    if spec.get("price_basis") not in ("user_authorized_temporary", "user_authorized", "user_set"):
        _fail("PRODUCT_PRICE_BASIS_INVALID")
    tags = spec.get("tags", [])
    if (not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() or len(tag) > 80 for tag in tags)
            or len(tags) != len(set(tags))):
        _fail("PRODUCT_TAGS_INVALID")
    variants = _option_rows(spec)

    upload_root = repo / "brands/agachichi/assets/media/uploads"
    manifest = _read_json(upload_root / "manifest.json", "PRODUCT_MEDIA_MANIFEST_INVALID")
    if manifest.get("environment") != "DEV":
        _fail("DEV_MEDIA_MANIFEST_REQUIRED")
    assets = manifest.get("assets")
    hero_rows = [row for row in assets if isinstance(row, dict) and row.get("product_id") == catalog_id] if isinstance(assets, list) else []
    if len(hero_rows) != 1 or hero_rows[0].get("status") != "READY":
        _fail("PRODUCT_HERO_MEDIA_INVALID")
    hero = hero_rows[0]
    hero_path = _verified_file(repo, upload_root, hero.get("target_path"), hero.get("sha256"), "PRODUCT_HERO_MEDIA_HASH_INVALID")

    gallery_doc = _read_json(upload_root / "gallery.json", "PRODUCT_GALLERY_MANIFEST_INVALID")
    if gallery_doc.get("environment") != "DEV" or gallery_doc.get("schema_version") != 1:
        _fail("DEV_GALLERY_MANIFEST_REQUIRED")
    gallery_assets = gallery_doc.get("assets")
    if not isinstance(gallery_assets, list):
        _fail("PRODUCT_GALLERY_MANIFEST_INVALID")
    gallery_rows = [row for row in gallery_assets if isinstance(row, dict) and row.get("product_id") == catalog_id]
    seen = set()
    gallery = []
    for row in gallery_rows:
        kind = row.get("kind")
        color_id = row.get("color_id")
        if kind not in GALLERY_KINDS:
            _fail("PRODUCT_GALLERY_KIND_INVALID")
        if color_id is not None and (kind not in {"model-front", "color-front"} or color_id not in {c["id"] for c in spec.get("color_options", [])}):
            _fail("PRODUCT_GALLERY_COLOR_INVALID")
        if kind == "color-front" and color_id is None:
            _fail("PRODUCT_GALLERY_COLOR_INVALID")
        key = (kind, color_id)
        if key in seen:
            _fail("PRODUCT_GALLERY_DUPLICATE")
        seen.add(key)
        extension = ".webp" if kind == "garment-cutout" else ".jpg"
        stem = catalog_id + ("-color-" + color_id if kind == "color-front" else "-" + kind)
        expected_relative = f"brands/agachichi/assets/media/uploads/gallery/{stem}{extension}"
        if row.get("path") != expected_relative:
            _fail("PRODUCT_GALLERY_PATH_INVALID")
        if type(row.get("ai_generated")) is not bool or row["ai_generated"] != (kind != "original"):
            _fail("PRODUCT_GALLERY_PROVENANCE_INVALID")
        asset_path = _verified_file(repo, upload_root / "gallery", row["path"], row.get("sha256"), "PRODUCT_GALLERY_HASH_INVALID")
        gallery.append({"kind": kind, "color_id": color_id, "path": str(asset_path), "sha256": row["sha256"], "ai_generated": row["ai_generated"]})
    if not all((kind, None) in seen for kind in REQUIRED_GALLERY_KINDS):
        _fail("PRODUCT_GALLERY_INCOMPLETE")
    gallery.sort(key=lambda row: (row["kind"], row["color_id"] or ""))

    media = [{"kind": "hero", "path": str(hero_path), "sha256": hero["sha256"]}]
    media.extend(gallery)
    return {
        "environment": "DEV",
        "catalog_id": catalog_id,
        "sku": "aicc-dev-" + catalog_id,
        "name": spec["name"].strip(),
        "description": spec["description"],
        "short_description": spec.get("style_tip", "") if isinstance(spec.get("style_tip", ""), str) else "",
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "tags": tags,
        "price": price,
        "sale_price": sale,
        "currency": "KRW",
        "price_status": "READY",
        "price_basis": spec["price_basis"],
        "inventory_pending": spec["inventory_pending"],
        "option_type": spec.get("option_type", "size"),
        "variants": variants,
        "media": media,
    }
