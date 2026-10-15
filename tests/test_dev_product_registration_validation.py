"""Standard-library tests for the deterministic DEV product intake validator."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "core/shopping/product_registration.py"
MODULE_SPEC = importlib.util.spec_from_file_location("product_registration_validation", MODULE_PATH)
VALIDATOR = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(VALIDATOR)


def put(root: Path, relative: str, data: bytes) -> str:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def fixture(root: Path, *, option_type="color", inventory=None, pending=True):
    pid = "ag-upload-outer-9001"
    colors = [{"id": "black", "label": "블랙"}, {"id": "ivory", "label": "아이보리"}]
    sizes = ["S", "M"]
    if option_type == "size":
        colors = []
        sizes = ["S", "M"]
        inventory = inventory if inventory is not None else {"S": 0, "M": 0}
    elif option_type == "color_size":
        inventory = inventory if inventory is not None else {
            f"{color['id']}--{size.lower()}": 0 for color in colors for size in sizes
        }
    else:
        inventory = inventory if inventory is not None else {"black": 0, "ivory": 0}
    spec = {
        "id": pid, "source": "user_upload", "name": "테스트 재킷",
        "description": "사진에서 확인되는 테스트 상품입니다.", "style_tip": "셔츠와 함께 연출해 보세요.",
        "category": "outer", "tags": ["재킷", "테스트"], "price_status": "READY",
        "price": 300000, "price_basis": "user_authorized_temporary", "currency": "KRW",
        "option_type": option_type, "color_options": colors, "size_options": sizes,
        "inventory": inventory, "inventory_pending": pending, "enabled": True,
    }
    catalog = {"schema_version": 1, "environment": "DEV", "products": [spec]}
    (root / "brands/agachichi/catalog/dev-upload-products.json").parent.mkdir(parents=True, exist_ok=True)
    (root / "brands/agachichi/catalog/dev-upload-products.json").write_text(json.dumps(catalog), encoding="utf-8")

    upload_root = root / "brands/agachichi/assets/media/uploads"
    hero_path = "brands/agachichi/assets/media/uploads/ag-upload-outer-9001.jpg"
    hero_sha = put(root, hero_path, b"hero-image")
    (upload_root / "manifest.json").write_text(json.dumps({
        "environment": "DEV",
        "assets": [{"product_id": pid, "status": "READY", "target_path": hero_path, "sha256": hero_sha}],
    }), encoding="utf-8")

    gallery = []
    gallery_root = "brands/agachichi/assets/media/uploads/gallery"
    for kind in ("original", "model-front", "garment-cutout", "model-other"):
        extension = ".webp" if kind == "garment-cutout" else ".jpg"
        relative = f"{gallery_root}/{pid}-{kind}{extension}"
        digest = put(root, relative, kind.encode())
        gallery.append({
            "product_id": pid, "kind": kind, "path": relative, "sha256": digest,
            "ai_generated": kind != "original",
        })
    (upload_root / "gallery.json").write_text(json.dumps({
        "schema_version": 1, "environment": "DEV", "assets": gallery,
    }), encoding="utf-8")
    return pid


class ProductRegistrationValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_color_product_binds_stock_and_all_gallery_roles(self):
        pid = fixture(self.root)
        product = VALIDATOR.validate_registration(self.root, pid)
        self.assertEqual(product["sku"], "aicc-dev-" + pid)
        self.assertEqual(len(product["variants"]), 2)
        self.assertEqual(product["variants"][0]["stock"], 0)
        self.assertEqual(len(product["media"]), 5)
        self.assertTrue(product["inventory_pending"])

    def test_pending_stock_must_be_zero(self):
        pid = fixture(self.root, inventory={"black": 1, "ivory": 0})
        with self.assertRaisesRegex(ValueError, "PENDING_INVENTORY_MUST_BE_ZERO"):
            VALIDATOR.validate_registration(self.root, pid)

    def test_catalog_option_keys_must_match_variation_matrix(self):
        pid = fixture(self.root, inventory={"black": 0})
        with self.assertRaisesRegex(ValueError, "PRODUCT_INVENTORY_OPTION_MISMATCH"):
            VALIDATOR.validate_registration(self.root, pid)

    def test_tampered_image_is_rejected(self):
        pid = fixture(self.root)
        image = self.root / "brands/agachichi/assets/media/uploads/ag-upload-outer-9001.jpg"
        image.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "PRODUCT_HERO_MEDIA_HASH_INVALID"):
            VALIDATOR.validate_registration(self.root, pid)

    def test_unknown_product_id_is_rejected(self):
        fixture(self.root)
        with self.assertRaisesRegex(ValueError, "PRODUCT_ID_INVALID"):
            VALIDATOR.validate_registration(self.root, "../not-a-product")

    def test_color_size_matrix_is_expanded_to_distinct_variants(self):
        pid = fixture(self.root, option_type="color_size")
        product = VALIDATOR.validate_registration(self.root, pid)
        self.assertEqual(len(product["variants"]), 4)
        self.assertEqual(product["variants"][0]["attributes"].keys(), {"color", "size"})

    def test_gallery_requires_full_visual_set(self):
        pid = fixture(self.root)
        manifest = self.root / "brands/agachichi/assets/media/uploads/gallery.json"
        doc = json.loads(manifest.read_text())
        doc["assets"] = [row for row in doc["assets"] if row["kind"] != "model-other"]
        manifest.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PRODUCT_GALLERY_INCOMPLETE"):
            VALIDATOR.validate_registration(self.root, pid)


if __name__ == "__main__":
    unittest.main()
