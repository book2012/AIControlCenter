"""Standard-library tests for staged single-product registration behavior."""
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dev_product_registration", ROOT / "ops/macos/shopping/dev_upload_product_register.py")
REGISTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REGISTER)


class RegistrationOperatorTests(unittest.TestCase):
    def test_default_cli_plan_is_read_only(self):
        output = io.StringIO()
        with patch.object(REGISTER, "REPO", ROOT), \
             patch.object(REGISTER, "assert_dev_isolation"), \
             patch.object(REGISTER, "_private_config", return_value={"environment": "DEV", "active_products": []}), \
             patch.object(REGISTER, "_woo_call", return_value={"environment": "DEV", "state": "SKU_AVAILABLE", "order_count": 4}), \
             patch.object(REGISTER, "_stage_media", side_effect=AssertionError("plan must not stage media")), \
             redirect_stdout(output):
            result = REGISTER.main(["--catalog-id", "ag-upload-outer-0006"])
        self.assertEqual(result, 0)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["environment"], "DEV")
        self.assertFalse(receipt["mutation"])
        self.assertFalse(receipt["activation"])
        self.assertEqual(receipt["sku_state"], "SKU_AVAILABLE")

    def test_woo_call_executes_php_harness_and_sends_payload_as_stdin(self):
        payload = {"environment": "DEV", "mode": "inspect", "catalog_id": "ag-upload-bottom-9001"}
        receipt = {"environment": "DEV", "state": "SKU_AVAILABLE", "order_count": 4}
        completed = REGISTER.subprocess.CompletedProcess([], 0, json.dumps(receipt), "")
        with patch.object(REGISTER, "_run", return_value=completed) as run:
            result = REGISTER._woo_call(payload)
        self.assertEqual(result, receipt)
        argv = run.call_args.args[0]
        self.assertEqual(argv[-2], "-r")
        self.assertIn("aicc_snapshot", argv[-1])
        self.assertEqual(json.loads(run.call_args.kwargs["input_text"]), payload)

    def test_existing_mapping_must_match_exactly(self):
        product = {"catalog_id": "ag-upload-outer-9001", "sku": "aicc-dev-ag-upload-outer-9001"}
        woo = {"state": "ALREADY_REGISTERED", "product": {"product_id": 901}}
        config = {"active_products": [{"demo_id": product["catalog_id"], "sku": product["sku"], "product_id": 901}]}
        REGISTER._validate_existing_mapping(config, product, woo)
        with self.assertRaisesRegex(RuntimeError, "DEV_PRODUCT_MAPPING_CONFLICT"):
            REGISTER._validate_existing_mapping(
                {"active_products": [{"demo_id": product["catalog_id"], "sku": product["sku"], "product_id": 902}]},
                product, woo,
            )

    def test_new_mapping_cannot_replace_existing_target(self):
        product = {"catalog_id": "ag-upload-outer-9001", "sku": "aicc-dev-ag-upload-outer-9001"}
        woo = {"state": "SKU_AVAILABLE"}
        config = {"active_products": [{"demo_id": product["catalog_id"], "sku": product["sku"], "product_id": 901}]}
        with self.assertRaisesRegex(RuntimeError, "DEV_PRODUCT_MAPPING_CONFLICT"):
            REGISTER._validate_existing_mapping(config, product, woo)

    def test_projection_candidate_preserves_existing_runtime_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "brands/agachichi/catalog/dev-upload-products.json"
            catalog_path.parent.mkdir(parents=True)
            existing_id, target_id = "ag-upload-top-9001", "ag-upload-outer-9001"
            catalog = {
                "schema_version": 1, "environment": "DEV", "products": [
                    {"id": existing_id, "enabled": True, "price": 100000, "sale_price": None},
                    {"id": target_id, "enabled": True, "price": 300000, "sale_price": None},
                ],
            }
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            runtime = root / "runtime"
            data = runtime / "data"
            data.mkdir(parents=True)
            projection_path = data / "product-projection.json"
            projection_path.write_text(json.dumps({
                "schema_version": 1, "environment": "DEV", "catalog_sha256": "a" * 64,
                "products": {existing_id: {
                    "enabled": True, "regular_price": 100000, "sale_price": None,
                    "inventory": {"S": 2, "M": 1},
                }},
            }), encoding="utf-8")
            projection_path.chmod(0o600)
            old_repo, old_runtime = REGISTER.REPO, REGISTER.RUNTIME
            REGISTER.REPO, REGISTER.RUNTIME = root, runtime
            try:
                product = {
                    "catalog_id": target_id, "price": 300000, "sale_price": None,
                    "variants": [{"key": "black", "stock": 0}, {"key": "ivory", "stock": 0}],
                }
                candidate, destination = REGISTER._projection_candidate(product)
                self.assertEqual(candidate["products"][existing_id]["inventory"], {"S": 2, "M": 1})
                self.assertEqual(candidate["products"][target_id]["inventory"], {"black": 0, "ivory": 0})
                self.assertEqual(candidate["catalog_sha256"], hashlib.sha256(catalog_path.read_bytes()).hexdigest())
                self.assertTrue(destination.name.endswith(f"{target_id}.candidate.json"))
            finally:
                REGISTER.REPO, REGISTER.RUNTIME = old_repo, old_runtime

    def test_projection_candidate_rejects_unrelated_stale_catalog_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "brands/agachichi/catalog/dev-upload-products.json"
            catalog_path.parent.mkdir(parents=True)
            target_id = "ag-upload-outer-9001"
            catalog_path.write_text(json.dumps({
                "schema_version": 1, "environment": "DEV",
                "products": [{"id": target_id, "enabled": True, "price": 300000, "sale_price": None}],
            }), encoding="utf-8")
            runtime = root / "runtime"
            data = runtime / "data"
            data.mkdir(parents=True)
            projection_path = data / "product-projection.json"
            projection_path.write_text(json.dumps({
                "schema_version": 1, "environment": "DEV", "catalog_sha256": "a" * 64,
                "products": {"ag-upload-top-9001": {
                    "enabled": True, "regular_price": 100000, "sale_price": None, "inventory": {"S": 1},
                }},
            }), encoding="utf-8")
            projection_path.chmod(0o600)
            old_repo, old_runtime = REGISTER.REPO, REGISTER.RUNTIME
            REGISTER.REPO, REGISTER.RUNTIME = root, runtime
            try:
                with self.assertRaisesRegex(RuntimeError, "DEV_PRODUCT_PROJECTION_SOURCE_UNRECOGNIZED"):
                    REGISTER._projection_candidate({
                        "catalog_id": target_id, "price": 300000, "sale_price": None,
                        "variants": [{"key": "black", "stock": 0}],
                    })
            finally:
                REGISTER.REPO, REGISTER.RUNTIME = old_repo, old_runtime


if __name__ == "__main__":
    unittest.main()
