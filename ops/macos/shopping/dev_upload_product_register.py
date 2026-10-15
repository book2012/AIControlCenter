"""Register one reviewed user-uploaded product in isolated DEV WooCommerce.

Default behavior is read-only. --apply-dev is the only path that creates a
WooCommerce product; it never activates the candidate or touches Production.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
PRIVATE = Path("/Users/kyouhan/.config/aicontrolcenter-dev-order")
RUNTIME = Path("/Users/kyouhan/AIControlCenterRuntime/dev-order")
DOCKER = ["docker", "--context", "colima-aicontrolcenter-commerce"]
WORDPRESS = "aicc-order-dev-wordpress-1"
DATABASE = "aicc-order-dev-database-1"
PHP = r'''<?php
if (getenv('WORDPRESS_DB_NAME') !== 'aicc_order_dev') { exit(2); }
require '/var/www/html/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/image.php';
add_filter('pre_wp_mail', function(){ return false; });
$cfg = json_decode(stream_get_contents(STDIN), true);
if (!is_array($cfg) || $cfg['environment'] !== 'DEV') { exit(3); }
global $wpdb;
$sku = $cfg['sku'];
$id = wc_get_product_id_by_sku($sku);
function aicc_snapshot($id, $cfg) {
  $p = wc_get_product($id);
  if (!$p || !$p->is_type('variable') || $p->get_sku() !== $cfg['sku']) { throw new Exception('PRODUCT_BINDING'); }
  if ($p->get_meta('_aicc_catalog_id') !== $cfg['catalog_id']
      || $p->get_meta('_aicc_source') !== 'user_upload'
      || $p->get_meta('_aicc_media_sha256') !== wp_json_encode(array_column($cfg['media'], 'sha256'))
      || $p->get_meta('_aicc_image_sha256') !== $cfg['media'][0]['sha256']
      || $p->get_meta('_aicc_inventory_pending') !== ($cfg['inventory_pending'] ? 'yes' : 'no')
      || $p->get_meta('_aicc_price_basis') !== $cfg['price_basis']
      || $p->get_meta('_aicc_price_status') !== 'READY'
      || $p->get_name() !== $cfg['name']
      || $p->get_description() !== $cfg['description']
      || $p->get_short_description() !== $cfg['short_description']
      || $p->get_status() !== 'publish') { throw new Exception('PRODUCT_CONTENT_BINDING'); }
  $imageIds = [];
  if ($p->get_image_id()) { $imageIds[] = $p->get_image_id(); }
  $imageIds = array_merge($imageIds, $p->get_gallery_image_ids());
  $hashes = [];
  foreach ($imageIds as $imageId) {
    $path = get_attached_file($imageId);
    $hashes[] = $path ? hash_file('sha256', $path) : '';
  }
  if ($hashes !== array_column($cfg['media'], 'sha256')) { throw new Exception('PRODUCT_MEDIA_BINDING'); }
  $terms = wp_get_post_terms($id, 'product_cat', ['fields'=>'slugs']);
  if (is_wp_error($terms) || !in_array($cfg['category'], $terms, true)) { throw new Exception('PRODUCT_CATEGORY_BINDING'); }
  $tagNames = wp_get_post_terms($id, 'product_tag', ['fields'=>'names']);
  if (is_wp_error($tagNames) || array_diff($cfg['tags'], $tagNames)) { throw new Exception('PRODUCT_TAG_BINDING'); }
  $variants = [];
  foreach ($p->get_children() as $variationId) {
    $v = wc_get_product($variationId);
    if (!$v || $v->get_status() !== 'publish' || !$v->managing_stock()
        || $v->get_backorders() !== 'no' || $v->get_stock_quantity() === null) { throw new Exception('PRODUCT_VARIANT_BINDING'); }
    $attributes = [];
    foreach ($v->get_attributes() as $key=>$value) { $attributes[strtolower($key)] = (string)$value; }
    $matches = [];
    foreach ($cfg['variants'] as $expected) {
      if ($attributes === $expected['attributes']) { $matches[] = $expected; }
    }
    if (count($matches) !== 1) { throw new Exception('PRODUCT_VARIANT_OPTIONS'); }
    $expected = $matches[0];
    if ($v->get_sku() !== $cfg['sku'] . '-' . sanitize_title($expected['key'])) { throw new Exception('PRODUCT_VARIANT_SKU'); }
    if ($v->get_stock_quantity() !== $expected['stock']
        || $v->get_regular_price() !== (string)$cfg['price']
        || $v->get_sale_price() !== ($cfg['sale_price'] === null ? '' : (string)$cfg['sale_price'])
        || $v->get_stock_status() !== ($expected['stock'] > 0 ? 'instock' : 'outofstock')) {
      throw new Exception('PRODUCT_VARIANT_VALUES');
    }
    $variants[$expected['key']] = (int)$variationId;
  }
  if (count($variants) !== count($cfg['variants'])) { throw new Exception('PRODUCT_VARIANT_COUNT'); }
  return ['product_id'=>(int)$id, 'sku'=>$sku, 'status'=>$p->get_status(),
          'variants'=>$variants, 'image_count'=>count($hashes)];
}
try {
  $beforeOrders = (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='shop_order'");
  if ($id) {
    $receipt = aicc_snapshot($id, $cfg);
    echo wp_json_encode(['environment'=>'DEV','state'=>'ALREADY_REGISTERED','order_count'=>$beforeOrders,'product'=>$receipt]);
    exit(0);
  }
  $catalogMatches = wc_get_products(['limit'=>2, 'return'=>'objects', 'meta_key'=>'_aicc_catalog_id', 'meta_value'=>$cfg['catalog_id']]);
  if (!$id && count($catalogMatches) > 0) { throw new Exception('CATALOG_ID_ALREADY_BOUND'); }
  if ($cfg['mode'] === 'inspect') {
    echo wp_json_encode(['environment'=>'DEV','state'=>'SKU_AVAILABLE','sku'=>$sku,'order_count'=>$beforeOrders]);
    exit(0);
  }
  foreach ($cfg['variants'] as $variant) {
    if (wc_get_product_id_by_sku($sku . '-' . sanitize_title($variant['key']))) { throw new Exception('VARIATION_SKU_ALREADY_USED'); }
  }
  $p = new WC_Product_Variable();
  $p->set_sku($sku); $p->set_name($cfg['name']); $p->set_description($cfg['description']);
  $p->set_short_description($cfg['short_description']); $p->set_status('draft');
  $term = term_exists($cfg['category'], 'product_cat');
  if (!$term) { $term = wp_insert_term($cfg['category_label'], 'product_cat', ['slug'=>$cfg['category']]); }
  if (is_wp_error($term)) { throw new Exception('PRODUCT_CATEGORY_CREATE'); }
  $p->set_category_ids([(int)(is_array($term) ? $term['term_id'] : $term)]);
  $tagIds = [];
  foreach ($cfg['tags'] as $tag) {
    $found = term_exists($tag, 'product_tag');
    if (!$found) { $found = wp_insert_term($tag, 'product_tag'); }
    if (is_wp_error($found)) { throw new Exception('PRODUCT_TAG_CREATE'); }
    $tagIds[] = (int)(is_array($found) ? $found['term_id'] : $found);
  }
  $p->set_tag_ids($tagIds);
  $attributes = [];
  $attributeLabels = [];
  foreach ($cfg['variants'] as $variant) {
    foreach ($variant['attributes'] as $key=>$value) { $attributeLabels[$key][$value] = $value; }
  }
  foreach ($attributeLabels as $key=>$labels) {
    $a = new WC_Product_Attribute();
    $a->set_id(0); $a->set_name(ucfirst($key)); $a->set_options(array_values($labels));
    $a->set_visible(true); $a->set_variation(true); $attributes[] = $a;
  }
  $p->set_attributes($attributes);
  $p->update_meta_data('_aicc_catalog_id', $cfg['catalog_id']);
  $p->update_meta_data('_aicc_source', 'user_upload');
  $p->update_meta_data('_aicc_image_sha256', $cfg['media'][0]['sha256']);
  $p->update_meta_data('_aicc_media_sha256', wp_json_encode(array_column($cfg['media'], 'sha256')));
  $p->update_meta_data('_aicc_price_status', 'READY');
  $p->update_meta_data('_aicc_price_basis', $cfg['price_basis']);
  $p->update_meta_data('_aicc_inventory_pending', $cfg['inventory_pending'] ? 'yes' : 'no');
  $id = $p->save();
  foreach ($cfg['variants'] as $variant) {
    $v = new WC_Product_Variation();
    $v->set_parent_id($id); $v->set_sku($sku . '-' . sanitize_title($variant['key']));
    $v->set_attributes($variant['attributes']); $v->set_regular_price((string)$cfg['price']);
    $v->set_sale_price($cfg['sale_price'] === null ? '' : (string)$cfg['sale_price']);
    $v->set_manage_stock(true); $v->set_stock_quantity($variant['stock']);
    $v->set_stock_status($variant['stock'] > 0 ? 'instock' : 'outofstock');
    $v->set_backorders('no'); $v->set_status('publish'); $v->save();
  }
  $attachmentIds = [];
  foreach ($cfg['media'] as $index=>$media) {
    $tmp = '/tmp/aicc-dev-product-registration/' . $cfg['catalog_id'] . '/asset-' . $index . $media['extension'];
    if (!is_file($tmp) || hash_file('sha256', $tmp) !== $media['sha256']) { throw new Exception('PRODUCT_MEDIA_STAGE'); }
    $attachment = media_handle_sideload(['name'=>$media['filename'], 'tmp_name'=>$tmp], $id, $cfg['name']);
    if (is_wp_error($attachment)) { throw new Exception('PRODUCT_MEDIA_ATTACH'); }
    $attachmentIds[] = (int)$attachment;
  }
  $p = wc_get_product($id); $p->set_image_id($attachmentIds[0]);
  $p->set_gallery_image_ids(array_slice($attachmentIds, 1)); $p->set_status('publish'); $p->save();
  WC_Product_Variable::sync($id); wc_delete_product_transients($id);
  $receipt = aicc_snapshot($id, $cfg);
  $afterOrders = (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='shop_order'");
  if ($beforeOrders !== $afterOrders) { throw new Exception('ORDER_COUNT_CHANGED'); }
  echo wp_json_encode(['environment'=>'DEV','state'=>'REGISTERED','order_count'=>$afterOrders,'product'=>$receipt]);
} catch (Throwable $e) {
  fwrite(STDERR, 'DEV_PRODUCT_REGISTRATION_FAILED');
  exit(4);
}
?>'''


def _run(argv: list[str], *, input_text: str | None = None, timeout: int = 30) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(argv, input=input_text, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("DEV_PRODUCT_OPERATION_UNAVAILABLE") from None


def assert_dev_isolation() -> None:
    result = _run(DOCKER + ["inspect", WORDPRESS, DATABASE], timeout=20)
    if result.returncode:
        raise RuntimeError("DEV_CONTAINERS_UNAVAILABLE")
    try:
        rows = json.loads(result.stdout)
        if len(rows) != 2:
            raise ValueError
        for row in rows:
            labels = row.get("Config", {}).get("Labels") or {}
            if labels.get("com.docker.compose.project") != "aicc-order-dev":
                raise ValueError
            volumes = {mount.get("Name") for mount in row.get("Mounts", []) if mount.get("Type") == "volume"}
            if not volumes or not volumes <= {"aicc-order-dev-wordpress", "aicc-order-dev-database"}:
                raise ValueError
            networks = row.get("NetworkSettings", {}).get("Networks") or {}
            if any(name.startswith("ai-shopping") for name in networks):
                raise ValueError
    except (ValueError, TypeError, KeyError):
        raise RuntimeError("DEV_ISOLATION_INVALID") from None


def _private_config() -> dict:
    path = PRIVATE / "runtime.private.json"
    if PRIVATE.is_symlink() or not PRIVATE.is_dir() or path.is_symlink() or not path.is_file():
        raise RuntimeError("DEV_PRIVATE_CONFIGURATION_INVALID")
    if path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise RuntimeError("DEV_PRIVATE_CONFIGURATION_INVALID")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise RuntimeError("DEV_PRIVATE_CONFIGURATION_INVALID") from None
    if (not isinstance(value, dict) or value.get("environment") != "DEV" or not isinstance(value.get("active_products"), list)
            or any(not isinstance(row, dict) for row in value["active_products"])):
        raise RuntimeError("DEV_PRIVATE_CONFIGURATION_INVALID")
    return value


def _woo_payload(product: dict, mode: str) -> dict:
    return {
        **product,
        "mode": mode,
        "category": product["category"],
        "media": [
            {
                **media,
                "filename": Path(media["path"]).name,
                "extension": Path(media["path"]).suffix,
                "container_path": f"/tmp/aicc-dev-product-registration/{product['catalog_id']}/asset-{index}{Path(media['path']).suffix}",
            }
            for index, media in enumerate(product["media"])
        ],
    }


def _woo_call(payload: dict, *, timeout: int = 90) -> dict:
    result = _run(DOCKER + ["exec", "-i", WORDPRESS, "php", "-d", "memory_limit=512M"],
                  input_text=json.dumps(payload, ensure_ascii=False), timeout=timeout)
    if result.returncode:
        raise RuntimeError("DEV_PRODUCT_REGISTRATION_FAILED_INSPECT_REQUIRED")
    try:
        output = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise RuntimeError("DEV_PRODUCT_REGISTRATION_RECEIPT_INVALID") from None
    if output.get("environment") != "DEV" or not isinstance(output.get("order_count"), int):
        raise RuntimeError("DEV_PRODUCT_REGISTRATION_RECEIPT_INVALID")
    return output


def _validate_existing_mapping(config: dict, product: dict, woo: dict) -> None:
    rows = [row for row in config["active_products"] if row.get("demo_id") == product["catalog_id"] or row.get("sku") == product["sku"]]
    if not rows:
        return
    if (woo.get("state") != "ALREADY_REGISTERED" or len(rows) != 1
            or rows[0].get("demo_id") != product["catalog_id"]
            or rows[0].get("sku") != product["sku"]
            or rows[0].get("product_id") != woo.get("product", {}).get("product_id")):
        raise RuntimeError("DEV_PRODUCT_MAPPING_CONFLICT")

def _projection_candidate(product: dict) -> tuple[dict, Path]:
    source = REPO / "brands/agachichi/catalog/dev-upload-products.json"
    catalog_bytes = source.read_bytes()
    catalog_hash = hashlib.sha256(catalog_bytes).hexdigest()
    catalog = json.loads(catalog_bytes)
    rows = catalog.get("products")
    if catalog.get("environment") != "DEV" or not isinstance(rows, list):
        raise RuntimeError("DEV_CATALOG_REQUIRED")
    expected_ids = {row["id"] for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}
    if len(expected_ids) != len(rows) or product["catalog_id"] not in expected_ids:
        raise RuntimeError("DEV_CATALOG_SCOPE_INVALID")

    data_root = RUNTIME / "data"
    current_path = data_root / "product-projection.json"
    if (RUNTIME.is_symlink() or data_root.is_symlink() or current_path.is_symlink()
            or not current_path.is_file() or current_path.stat().st_uid != os.getuid()
            or current_path.stat().st_mode & 0o077):
        raise RuntimeError("DEV_PRODUCT_PROJECTION_INVALID")
    current = json.loads(current_path.read_text(encoding="utf-8"))
    if not isinstance(current, dict):
        raise RuntimeError("DEV_PRODUCT_PROJECTION_INVALID")
    projection_rows = current.get("products")
    if current.get("schema_version") != 1 or current.get("environment") != "DEV" or not isinstance(projection_rows, dict):
        raise RuntimeError("DEV_PRODUCT_PROJECTION_INVALID")
    target_id = product["catalog_id"]
    target_row = {
        "enabled": True,
        "regular_price": product["price"],
        "sale_price": product["sale_price"],
        "inventory": {variant["key"]: variant["stock"] for variant in product["variants"]},
    }
    if current.get("catalog_sha256") == catalog_hash:
        if set(projection_rows) != expected_ids or projection_rows.get(target_id) != target_row:
            raise RuntimeError("DEV_PRODUCT_PROJECTION_BINDING_INVALID")
        candidate_rows = dict(projection_rows)
    else:
        if set(projection_rows) != expected_ids - {target_id}:
            raise RuntimeError("DEV_PRODUCT_PROJECTION_SOURCE_UNRECOGNIZED")
        by_id = {row["id"]: row for row in rows}
        for pid, projection in projection_rows.items():
            catalog_row = by_id[pid]
            if (not isinstance(projection, dict)
                    or projection.get("enabled") != catalog_row.get("enabled", True)
                    or projection.get("regular_price") != catalog_row.get("price")
                    or projection.get("sale_price") != catalog_row.get("sale_price")):
                raise RuntimeError("DEV_PRODUCT_PROJECTION_SOURCE_UNRECOGNIZED")
        candidate_rows = dict(projection_rows)
        candidate_rows[target_id] = target_row
    candidate = {
        "schema_version": 1,
        "environment": "DEV",
        "catalog_sha256": catalog_hash,
        "products": candidate_rows,
    }
    candidate_path = current_path.with_name(f"product-projection-{target_id}.candidate.json")
    return candidate, candidate_path


def _stage_candidate(product: dict, woo: dict) -> None:
    config = _private_config()
    projection, projection_path = _projection_candidate(product)
    active = config["active_products"]
    existing = [row for row in active if row.get("demo_id") == product["catalog_id"] or row.get("product_id") == woo["product"]["product_id"]]
    if existing:
        row = existing[0]
        if len(existing) != 1 or row.get("demo_id") != product["catalog_id"] or row.get("product_id") != woo["product"]["product_id"]:
            raise RuntimeError("DEV_PRODUCT_MAPPING_CONFLICT")
    variants = []
    for variant in product["variants"]:
        variants.append({
            "id": woo["product"]["variants"][variant["key"]],
            "label": variant["label"],
            "available": variant["stock"] > 0 and not product["inventory_pending"],
            "stock": variant["stock"],
        })
    binding = {
        "demo_id": product["catalog_id"],
        "product_id": woo["product"]["product_id"],
        "sku": product["sku"],
        "category": product["category_label"],
        "image_demo_id": product["catalog_id"],
        "option_type": product["option_type"],
        "inventory_pending": product["inventory_pending"],
        "variants": variants,
    }
    candidate = dict(config)
    candidate["active_products"] = [
        row for row in active
        if row.get("demo_id") != product["catalog_id"] and row.get("product_id") != woo["product"]["product_id"]
    ] + [binding]
    if PRIVATE.is_symlink() or RUNTIME.is_symlink():
        raise RuntimeError("DEV_PRODUCT_CANDIDATE_INVALID")
    PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(PRIVATE, 0o700)
    os.chmod(RUNTIME, 0o700)
    target = PRIVATE / f"runtime.product-registration-{product['catalog_id']}.candidate.private.json"
    if target.is_symlink():
        raise RuntimeError("DEV_PRODUCT_CANDIDATE_INVALID")
    if target.exists():
        if json.loads(target.read_text(encoding="utf-8")) != candidate:
            raise RuntimeError("DEV_PRODUCT_CANDIDATE_CONFLICT")
    else:
        _private_write(target, candidate)
    evidence = {
        "environment": "DEV",
        "catalog_id": product["catalog_id"],
        "product_id": woo["product"]["product_id"],
        "sku": product["sku"],
        "price": product["price"],
        "inventory_pending": product["inventory_pending"],
        "variants": variants,
        "image_count": len(product["media"]),
        "image_sha256": [row["sha256"] for row in product["media"]],
        "prod_mutation": False,
        "activation": False,
    }
    if projection_path.is_symlink():
        raise RuntimeError("DEV_PRODUCT_PROJECTION_CANDIDATE_INVALID")
    if projection_path.exists():
        if json.loads(projection_path.read_text(encoding="utf-8")) != projection:
            raise RuntimeError("DEV_PRODUCT_PROJECTION_CANDIDATE_CONFLICT")
    else:
        _private_write(projection_path, projection)
    evidence_path = RUNTIME / f"product-registration-{product['catalog_id']}-evidence.json"
    RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    if evidence_path.is_symlink():
        raise RuntimeError("DEV_PRODUCT_EVIDENCE_INVALID")
    if evidence_path.exists():
        if json.loads(evidence_path.read_text(encoding="utf-8")) != evidence:
            raise RuntimeError("DEV_PRODUCT_EVIDENCE_CONFLICT")
    else:
        _private_write(evidence_path, evidence)


def _private_write(path: Path, value: dict) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".product-registration-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _stage_media(product: dict) -> None:
    container_root = f"/tmp/aicc-dev-product-registration/{product['catalog_id']}"
    result = _run(DOCKER + ["exec", WORDPRESS, "mkdir", "-p", container_root])
    if result.returncode:
        raise RuntimeError("DEV_PRODUCT_MEDIA_STAGE_FAILED")
    for index, media in enumerate(product["media"]):
        source = media["path"]
        target = f"{WORDPRESS}:{container_root}/asset-{index}{Path(source).suffix}"
        result = _run(DOCKER + ["cp", source, target], timeout=30)
        if result.returncode:
            raise RuntimeError("DEV_PRODUCT_MEDIA_STAGE_FAILED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-id", required=True, help="DEV upload catalog id (ag-upload-<category>-NNNN)")
    parser.add_argument("--apply-dev", action="store_true", help="Create in isolated DEV WooCommerce and stage a private candidate")
    args = parser.parse_args(argv)
    try:
        validator_path = REPO / "core/shopping/product_registration.py"
        validator_spec = importlib.util.spec_from_file_location("aicc_product_registration_validation", validator_path)
        if validator_spec is None or validator_spec.loader is None:
            raise RuntimeError("PRODUCT_VALIDATOR_UNAVAILABLE")
        validator = importlib.util.module_from_spec(validator_spec)
        validator_spec.loader.exec_module(validator)
        product = validator.validate_registration(REPO, args.catalog_id)
        assert_dev_isolation()
        runtime_config = _private_config()
        inspect_payload = _woo_payload(product, "inspect")
        inspected = _woo_call(inspect_payload, timeout=60)
        if inspected.get("state") not in {"SKU_AVAILABLE", "ALREADY_REGISTERED"}:
            raise RuntimeError("DEV_PRODUCT_REGISTRATION_STATE_INVALID")
        _validate_existing_mapping(runtime_config, product, inspected)
        if not args.apply_dev:
            print(json.dumps({
                "environment": "DEV",
                "catalog_id": product["catalog_id"],
                "sku": product["sku"],
                "price": product["price"],
                "option_count": len(product["variants"]),
                "inventory_pending": product["inventory_pending"],
                "image_count": len(product["media"]),
                "sku_state": inspected["state"],
                "mutation": False,
                "activation": False,
            }, ensure_ascii=False))
            return 0
        if inspected["state"] == "SKU_AVAILABLE":
            _stage_media(product)
            result = _woo_call(_woo_payload(product, "apply"), timeout=180)
        else:
            result = inspected
        if result.get("state") not in {"REGISTERED", "ALREADY_REGISTERED"}:
            raise RuntimeError("DEV_PRODUCT_REGISTRATION_STATE_INVALID")
        _stage_candidate(product, result)
        print(json.dumps({
            "environment": "DEV",
            "catalog_id": product["catalog_id"],
            "product_id": result["product"]["product_id"],
            "sku": product["sku"],
            "state": result["state"],
            "candidate_staged": True,
            "inventory_pending": product["inventory_pending"],
            "order_count_unchanged": True,
            "prod_mutation": False,
            "activation": False,
        }, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        print(json.dumps({"error": "DEV_PRODUCT_REGISTRATION_BLOCKED", "mutation": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
