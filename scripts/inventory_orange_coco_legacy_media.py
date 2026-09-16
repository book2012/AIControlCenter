"""Create a conservative deletion-candidate inventory for legacy demo photos."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products"
CATALOG = ROOT / "brands/orange-coco/catalog/catalog.json"
OUT = ROOT / "docs/architecture/SHOP-MEDIA-002R1-LEGACY-DELETION-CANDIDATES.json"

def main():
    products = json.loads(CATALOG.read_text())["products"]
    canonical = {item["image_path"] for item in products}
    rows = []
    for path in sorted(LEGACY.glob("*/*.jpg")):
        relative = path.relative_to(ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1")
        image_path = "wp-content/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/" + str(relative)
        rows.append({"path": str(path.relative_to(ROOT)), "referenced_by_canonical_catalog": image_path in canonical,
                     "deletion_candidate": False,
                     "reason": "Canonical demo catalog and regression fixtures still require this compatibility asset."})
    OUT.write_text(json.dumps({"policy": "SHOP_MEDIA_002R1", "legacy_fallback_active": False,
                               "safe_to_delete_now": 0, "candidates": rows}, ensure_ascii=False, indent=2) + "\n")
    print(f"Inventoried {len(rows)} legacy files; safe_to_delete_now=0")

if __name__ == "__main__":
    main()
