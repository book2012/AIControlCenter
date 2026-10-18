"""Tests for review-gated Codex product intake and DEV registration."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dev_codex_product_intake",
    ROOT / "ops/macos/shopping/dev_codex_product_intake.py",
)
INTAKE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INTAKE_MODULE)
DevProductIntake = INTAKE_MODULE.DevProductIntake
ProductIntakeError = INTAKE_MODULE.ProductIntakeError
MEDIA = INTAKE_MODULE.MEDIA
JOB = "deadbeef"


def fields():
    return {
        "name": "검토 상품",
        "category": "bottom",
        "description": "운영자가 확인한 상품 설명입니다.",
        "style_tip": "확인된 스타일 안내입니다.",
        "price": 79000,
        "sale_price": None,
        "price_basis": "user_set",
        "tags": ["검토"],
        "option_type": "color",
        "color_options": [{"id": "beige", "label": "베이지"}],
        "size_options": [],
        "inventory": {"beige": 0},
        "inventory_pending": True,
    }


def image(role):
    if role == "garment-cutout":
        return b"RIFFxxxxWEBPsample"
    return b"\xff\xd8\xffsample-jpeg"


def make_source(root):
    source = root / "source"
    (source / "brands/agachichi/catalog").mkdir(parents=True)
    (source / "brands/agachichi/assets/media/uploads").mkdir(parents=True)
    (source / "brands/agachichi/catalog/dev-upload-products.json").write_text(
        json.dumps({"schema_version": 1, "environment": "DEV", "products": []}),
        encoding="utf-8",
    )
    upload = source / "brands/agachichi/assets/media/uploads"
    (upload / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "environment": "DEV", "assets": []}),
        encoding="utf-8",
    )
    (upload / "gallery.json").write_text(
        json.dumps({"schema_version": 1, "environment": "DEV", "assets": []}),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-qm", "fixture"], check=True)
    revision = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    return source, revision


def make_intake(root):
    source, revision = make_source(root)
    intake = DevProductIntake(root=root / "private", source=source, revision=revision)
    intake.save_review(JOB, fields())
    for role in MEDIA:
        ext, content_type, _ = MEDIA[role]
        body = image(role)
        intake.upload_media(
            JOB, role, body, content_type=content_type,
            filename=role + ext, ai_generated=(role in {"garment-cutout"}),
        )
    return intake


class DevCodexProductIntakeTests(unittest.TestCase):
    def test_invalid_image_signature_is_rejected_and_upload_is_private(self):
        with tempfile.TemporaryDirectory() as temp:
            source, revision = make_source(Path(temp))
            intake = DevProductIntake(root=Path(temp) / "private", source=source, revision=revision)
            with self.assertRaisesRegex(ProductIntakeError, "PRODUCT_MEDIA_SIGNATURE_INVALID"):
                intake.upload_media(JOB, "hero", b"not an image", content_type="image/jpeg", filename="x.jpg", ai_generated=False)
            body = image("hero")
            result = intake.upload_media(JOB, "hero", body, content_type="image/jpeg", filename="sample.jpg", ai_generated=False)
            path = Path(temp) / "private" / JOB / "media-hero.jpg"
            self.assertEqual(result["sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual((Path(temp) / "private").stat().st_mode & 0o777, 0o700)

    def test_workspace_materializes_review_fields_and_verified_media_for_existing_validator(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            intake = make_intake(root)
            meta = intake._read_meta(intake._job_dir(JOB))
            workspace = root / "workspace"
            workspace.mkdir()
            catalog_id = intake._workspace(JOB, meta, workspace)
            validator_spec = importlib.util.spec_from_file_location(
                "product_registration_for_intake_test",
                ROOT / "core/shopping/product_registration.py",
            )
            validator = importlib.util.module_from_spec(validator_spec)
            validator_spec.loader.exec_module(validator)
            product = validator.validate_registration(workspace, catalog_id)
            self.assertEqual(catalog_id, "ag-upload-bottom-0001")
            self.assertEqual(product["price"], 79000)
            self.assertEqual(len(product["media"]), 5)
            self.assertFalse(next(v for v in product["media"] if v.get("kind") == "model-front")["ai_generated"])
            self.assertTrue(next(v for v in product["media"] if v.get("kind") == "garment-cutout")["ai_generated"])

    def test_concurrent_product_intakes_reserve_distinct_catalog_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, revision = make_source(root)
            intake = DevProductIntake(root=root / "private", source=source, revision=revision)
            for job in (JOB, "beadfeed"):
                intake.save_review(job, fields())
                for role in MEDIA:
                    ext, content_type, _ = MEDIA[role]
                    intake.upload_media(job, role, image(role), content_type=content_type,
                        filename=role + ext, ai_generated=(role == "garment-cutout"))
            intake._workspace = lambda job, meta, workspace: meta["catalog_id"]

            def fake_runner(argv, **kwargs):
                payload = {"environment": "DEV", "state": "SKU_AVAILABLE", "sku_state": "SKU_AVAILABLE",
                           "mutation": False, "activation": False}
                return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

            intake.runner = fake_runner
            first = intake.preflight(JOB)
            second = intake.preflight("beadfeed")
            self.assertEqual(first["catalog_id"], "ag-upload-bottom-0001")
            self.assertEqual(second["catalog_id"], "ag-upload-bottom-0002")

    def test_dev_registration_requires_preflight_and_exact_name_then_applies_once(self):
        with tempfile.TemporaryDirectory() as temp:
            intake = make_intake(Path(temp))
            calls = []

            def fake_workspace(job_id, meta, workspace):
                return "ag-upload-bottom-0001"

            def fake_runner(argv, **kwargs):
                calls.append(argv)
                applying = "--apply-dev" in argv
                payload = ({"environment": "DEV", "state": "REGISTERED", "prod_mutation": False, "activation": False}
                           if applying else {"environment": "DEV", "state": "SKU_AVAILABLE", "sku": "aicc-dev-test",
                                             "mutation": False, "activation": False, "sku_state": "SKU_AVAILABLE"})
                return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

            intake._workspace = fake_workspace
            intake.runner = fake_runner
            with self.assertRaisesRegex(ProductIntakeError, "PRODUCT_PREFLIGHT_REQUIRED"):
                intake.register(JOB, "검토 상품")
            ready = intake.preflight(JOB)
            self.assertEqual(ready["state"], "READY_TO_REGISTER")
            with self.assertRaisesRegex(ProductIntakeError, "PRODUCT_CONFIRMATION_MISMATCH"):
                intake.register(JOB, "다른 이름")
            self.assertEqual(len(calls), 1)
            result = intake.register(JOB, "검토 상품")
            self.assertEqual(result["state"], "REGISTERED")
            self.assertTrue(any("--apply-dev" in argv for argv in calls))
            self.assertEqual(intake.register(JOB, "검토 상품")["state"], "REGISTERED")
            self.assertEqual(len(calls), 2)

    def test_uncertain_apply_outcome_cannot_be_retried_automatically(self):
        with tempfile.TemporaryDirectory() as temp:
            intake = make_intake(Path(temp))
            calls = []

            def fake_workspace(job_id, meta, workspace):
                return "ag-upload-bottom-0001"

            def fake_runner(argv, **kwargs):
                calls.append(argv)
                if "--apply-dev" in argv:
                    raise TimeoutError("simulated timeout after apply started")
                payload = {"environment": "DEV", "state": "SKU_AVAILABLE", "mutation": False, "activation": False, "sku_state": "SKU_AVAILABLE"}
                return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

            intake._workspace = fake_workspace
            intake.runner = fake_runner
            intake.preflight(JOB)
            with self.assertRaisesRegex(ProductIntakeError, "APPLY_OUTCOME_UNKNOWN"):
                intake.register(JOB, "검토 상품")
            before = len(calls)
            self.assertEqual(intake.status(JOB)["state"], "APPLY_OUTCOME_UNKNOWN")
            with self.assertRaisesRegex(ProductIntakeError, "APPLY_OUTCOME_UNKNOWN"):
                intake.register(JOB, "검토 상품")
            self.assertEqual(len(calls), before)


if __name__ == "__main__":
    unittest.main()
