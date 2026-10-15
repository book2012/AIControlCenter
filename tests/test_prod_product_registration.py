from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "ops/macos/shopping/prod_upload_product_register.py"
    spec = importlib.util.spec_from_file_location("prod_upload_product_register_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    path.chmod(0o600)


def test_prod_registration_stages_separate_zero_stock_bindings(tmp_path, monkeypatch):
    module = _module()
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(module, "REPO", repo)
    private = tmp_path / "private"
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(module, "PRIVATE", private)
    monkeypatch.setattr(module, "RUNTIME", runtime)

    catalog_path = repo / "brands/agachichi/catalog/dev-upload-products.json"
    catalog = json.loads(catalog_path.read_text())
    ids = [row["id"] for row in catalog["products"]]
    existing_ids = [pid for pid in ids if pid not in {"ag-upload-bottom-0002", "ag-upload-outer-0006"}]
    bindings = [
        {"demo_id": pid, "product_id": index + 1, "sku": "aicc-prod-" + pid,
         "category": "OUTER", "option_type": "size"}
        for index, pid in enumerate(existing_ids)
    ]
    config = {"environment": "PROD", "bindings": bindings, "shipping_policy": "PROD_INCLUDED_SHIPPING",
              "binding_key": "a" * 64, "csrf_key": "b" * 64, "port_credentials": []}
    _write(private / "runtime.private.json", config)

    projection = {
        "schema_version": 1, "environment": "PROD", "catalog_sha256": "old-catalog",
        "products": {
            pid: {"enabled": True, "regular_price": 10000, "sale_price": None, "inventory": {"S": 1}}
            for pid in existing_ids
        },
    }
    _write(runtime / "data/product-projection.json", projection)
    original_config = (private / "runtime.private.json").read_bytes()
    original_projection = (runtime / "data/product-projection.json").read_bytes()

    for pid,woo_id in [("ag-upload-bottom-0002",116),("ag-upload-outer-0006",122)]:
        row = next(item for item in catalog["products"] if item["id"] == pid)
        product = {"catalog_id": pid, "price": row["price"], "sale_price": None,
                   "category_label": row["category_label"], "option_type": row["option_type"],
                   "variants": [{"key": key, "stock": value} for key,value in row["inventory"].items()],
                       "media": []}
        module.stage_binding(product, {"product": {"product_id": woo_id}})

    candidate = json.loads((private / "runtime.product-registration.candidate.private.json").read_text())
    new_rows = [b for b in candidate["bindings"] if b["demo_id"] in {"ag-upload-bottom-0002","ag-upload-outer-0006"}]
    assert {b["demo_id"] for b in new_rows} == {"ag-upload-bottom-0002","ag-upload-outer-0006"}
    assert {b["product_id"] for b in new_rows} == {116,122}
    assert all(b["sku"].startswith("aicc-prod-") for b in new_rows)
    assert (private / "runtime.private.json").read_bytes() == original_config
    assert (runtime / "data/product-projection.json").read_bytes() == original_projection

    projected = json.loads((runtime / "data/product-projection.candidate.json").read_text())
    assert projected["environment"] == "PROD"
    assert set(projected["products"]) == set(ids)
    assert projected["products"]["ag-upload-bottom-0002"]["inventory"] == {"beige":0}
    assert projected["products"]["ag-upload-outer-0006"]["inventory"] == {"charcoal":0}


def test_production_registration_php_targets_only_prod_store():
    module = _module()
    php = module.registration_php()
    assert "aicc_shopping" in php
    assert "'environment'] !== 'PROD'" in php
    assert "/tmp/aicc-prod-product-registration/" in php
    assert "/tmp/aicc-dev-product-registration/" not in php
    assert "order_count_before" in php
