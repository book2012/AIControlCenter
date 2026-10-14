"""Verify one DEV user-uploaded Woo product and stage its private runtime binding.

WooCommerce is read-only here. --apply-dev writes only the isolated DEV runtime
candidate and evidence; product writes remain behind reviewed Woo registrars.
"""
from pathlib import Path
import argparse, base64, hashlib, json, subprocess, sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ops.macos.shopping.dev_order_provision import PRIVATE, RUNTIME, private_write
from ops.macos.shopping.dev_order_runtime import assert_isolation

REPO = Path(__file__).resolve().parents[3]
CATALOG_ID = "ag-upload-outer-0006"
SKU = "aicc-dev-" + CATALOG_ID
PRICE = 300000
DOCKER = ["docker", "--context", "colima-aicontrolcenter-commerce"]
CONTAINER = "aicc-order-dev-wordpress-1"

PHP = r'''<?php
if (getenv('WORDPRESS_DB_NAME') !== 'aicc_order_dev') { exit(2); }
require '/var/www/html/wp-load.php';
$id = wc_get_product_id_by_sku('aicc-dev-ag-upload-outer-0006');
$p = $id ? wc_get_product($id) : false;
if (!$p || !$p->is_type('variable')) { exit(3); }
$children = $p->get_children();
$variants = [];
foreach ($children as $vid) {
  $v = wc_get_product($vid);
  $attrs = $v ? $v->get_attributes() : [];
  $variants[] = [
    'id' => (int)$vid,
    'label' => (string)($attrs['color'] ?? ''),
    'price' => $v ? $v->get_regular_price() : '',
    'stock' => $v ? $v->get_stock_quantity() : null,
    'manage_stock' => $v ? $v->managing_stock() : false,
    'stock_status' => $v ? $v->get_stock_status() : '',
    'backorders' => $v ? $v->get_backorders() : '',
    'status' => $v ? $v->get_status() : ''
  ];
}
$img = $p->get_image_id();
global $wpdb;
echo wp_json_encode([
  'order_count' => (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='shop_order'"),
  'product_id' => (int)$id, 'status' => $p->get_status(),
  'sku' => $p->get_sku(), 'name' => $p->get_name(),
  'price' => $p->get_price(), 'price_status' => $p->get_meta('_aicc_price_status'),
  'price_basis' => $p->get_meta('_aicc_price_basis'),
  'source' => $p->get_meta('_aicc_source'),
  'catalog_id' => $p->get_meta('_aicc_catalog_id'),
  'image_sha256' => $p->get_meta('_aicc_image_sha256'),
  'inventory_pending' => $p->get_meta('_aicc_inventory_pending'),
  'image_id' => (int)$img,
  'attached_sha256' => $img ? hash_file('sha256', get_attached_file($img)) : '',
  'categories' => wp_get_post_terms($id, 'product_cat', ['fields'=>'names']),
  'tags' => wp_get_post_terms($id, 'product_tag', ['fields'=>'names']),
  'variants' => $variants
], JSON_UNESCAPED_UNICODE);
?>'''

def read_spec():
    doc = json.loads((REPO / "brands/agachichi/catalog/dev-upload-products.json").read_text())
    if doc.get("environment") != "DEV":
        raise RuntimeError("DEV_CATALOG_REQUIRED")
    rows = [r for r in doc.get("products", []) if r.get("id") == CATALOG_ID]
    if len(rows) != 1:
        raise RuntimeError("PRODUCT_ID_NOT_UNIQUE")
    spec = rows[0]
    if (spec.get("registration_method") != "single_product"
            or spec.get("price") != PRICE or spec.get("price_status") != "READY"
            or spec.get("price_basis") != "user_authorized_temporary"
            or spec.get("inventory_pending") is not True
            or spec.get("inventory") != {"charcoal": 0}
            or spec.get("color_options") != [{"id":"charcoal","label":"차콜"}]):
        raise RuntimeError("PRODUCT_SPEC_INVALID")
    manifest = json.loads((REPO / "brands/agachichi/assets/media/uploads/manifest.json").read_text())
    assets = [a for a in manifest.get("assets", []) if a.get("product_id") == CATALOG_ID]
    if len(assets) != 1 or assets[0].get("status") != "READY":
        raise RuntimeError("PRODUCT_MEDIA_MANIFEST_INVALID")
    image = (REPO / assets[0]["target_path"]).resolve()
    media_root = (REPO / "brands/agachichi/assets/media/uploads").resolve()
    if (not image.is_relative_to(media_root) or image.is_symlink() or not image.is_file()
            or hashlib.sha256(image.read_bytes()).hexdigest() != assets[0].get("sha256")):
        raise RuntimeError("PRODUCT_MEDIA_HASH_INVALID")
    return spec, assets[0]["sha256"]

def read_woo(spec, sha):
    payload = base64.b64encode(json.dumps({"id": CATALOG_ID}).encode()).decode()
    proc = subprocess.run(
        DOCKER + ["exec", "-i", CONTAINER, "php", "-d", "memory_limit=256M"],
        input=PHP.replace("aicc-dev-ag-upload-outer-0006", SKU),
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode:
        raise RuntimeError("DEV_PRODUCT_READ_FAILED")
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        raise RuntimeError("DEV_PRODUCT_READ_INVALID") from None
    variants = data.get("variants", [])
    if (data.get("sku") != SKU or data.get("catalog_id") != CATALOG_ID
            or data.get("status") != "publish" or data.get("price") != str(PRICE)
            or data.get("price_status") != "READY"
            or data.get("price_basis") != "user_authorized_temporary"
            or data.get("source") != "user_upload"
            or data.get("inventory_pending") != "yes"
            or data.get("image_sha256") != sha or data.get("attached_sha256") != sha
            or data.get("image_id", 0) < 1 or len(variants) != 1):
        raise RuntimeError("DEV_PRODUCT_BINDING_INVALID")
    v = variants[0]
    if (v.get("label") != "차콜" or v.get("price") != str(PRICE)
            or v.get("stock") != 0 or v.get("manage_stock") is not True
            or v.get("stock_status") != "outofstock" or v.get("backorders") != "no"
            or v.get("status") != "publish"):
        raise RuntimeError("DEV_PRODUCT_VARIANT_INVALID")
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-dev", action="store_true", help="Stage private DEV mapping; never mutates WooCommerce")
    args = parser.parse_args()
    assert_isolation()
    spec, sha = read_spec()
    woo = read_woo(spec, sha)
    current_path = PRIVATE / "runtime.private.json"
    candidate_path = PRIVATE / "runtime.batch-candidate.private.json"
    current = json.loads(current_path.read_text())
    candidate = json.loads(candidate_path.read_text()) if candidate_path.exists() else current
    if current.get("environment") != "DEV" or candidate.get("environment") != "DEV":
        raise RuntimeError("DEV_RUNTIME_REQUIRED")
    active = candidate.get("active_products")
    if not isinstance(active, list) or len(active) < 5:
        raise RuntimeError("DEV_ACTIVE_PRODUCTS_REQUIRED")
    binding = {
        "demo_id": CATALOG_ID, "product_id": woo["product_id"], "sku": SKU,
        "category": "OUTER", "image_demo_id": CATALOG_ID, "option_type": "color",
        "inventory_pending": True,
        "variants": [{"id": woo["variants"][0]["id"], "label": "차콜", "available": False, "stock": 0}],
    }
    matches = [x for x in active if x.get("demo_id") == CATALOG_ID or x.get("product_id") == woo["product_id"]]
    if matches and (len(matches) != 1 or matches[0].get("demo_id") != CATALOG_ID
                    or matches[0].get("product_id") != woo["product_id"]):
        raise RuntimeError("DEV_MAPPING_CONFLICT")
    if not args.apply_dev:
        print(json.dumps({"environment":"DEV","catalog_id":CATALOG_ID,
                          "product_id":woo["product_id"],"price":PRICE,
                          "stock":0,"inventory_pending":True,"mutation":False}))
        return
    candidate["active_products"] = [x for x in active if x.get("demo_id") != CATALOG_ID
                                    and x.get("product_id") != woo["product_id"]] + [binding]
    private_write(candidate_path, candidate)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    private_write(RUNTIME / "upload-product-staging-evidence.json", {
        "environment":"DEV","catalog_id":CATALOG_ID,"product_id":woo["product_id"],
        "price":PRICE,"status":"publish","inventory":{"charcoal":0},
        "inventory_pending":True,"available":False,"active_product_count":len(candidate["active_products"]),
        "order_count_at_stage":woo["order_count"],"production_mutation":False,
    })
    print(json.dumps({"environment":"DEV","staged":True,"catalog_id":CATALOG_ID,
                      "product_id":woo["product_id"],"candidate_product_count":len(candidate["active_products"]),
                      "available":False,"production_mutation":False}))

if __name__ == "__main__":
    main()
