"""Promote one validated user-uploaded product to orderable isolated DEV commerce."""
from pathlib import Path
import base64,hashlib,json,subprocess,sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from ops.macos.shopping.dev_order_provision import PRIVATE,RUNTIME,private_write
from ops.macos.shopping.dev_order_runtime import assert_isolation

REPO=Path(__file__).resolve().parents[3]
CATALOG_ID="ag-upload-outer-0001"
TARGET_PRICE=300000
SKU="aicc-dev-"+CATALOG_ID
DOCKER=["docker","--context","colima-aicontrolcenter-commerce"]
CONTAINER="aicc-order-dev-wordpress-1"

PHP=r'''<?php
if (getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev') { exit(2); }
require '/var/www/html/wp-load.php';
$spec=json_decode(base64_decode('__PAYLOAD__'),true);
if(!is_array($spec) || $spec['id']!=='ag-upload-outer-0001' || $spec['price_status']!=='READY' || (int)$spec['price']!==300000){exit(3);}
$id=wc_get_product_id_by_sku('aicc-dev-ag-upload-outer-0001');
$product=$id?wc_get_product($id):false;
if(!$product || !$product->is_type('variable') || $product->get_sku()!=='aicc-dev-ag-upload-outer-0001'){exit(4);}
$current=get_post_meta($id,'_aicc_price_status',true);
if(!in_array($current,['PENDING','READY'],true)){exit(5);}
$children=$product->get_children();
$by_label=[];
foreach($children as $vid){
  $v=wc_get_product($vid);if(!$v){continue;}
  $label=$v->get_attribute('size');
  if($label===''){$attrs=$v->get_attributes();$label=(string)($attrs['size']??reset($attrs));}
  if($label!==''){$by_label[$label]=$v;}
}
if(array_keys($spec['inventory'])!==['S','M','L'] || count($by_label)!==3){exit(6);}
foreach($spec['inventory'] as $label=>$expected_stock){
  if(!isset($by_label[$label])){exit(7);}
  $variant=$by_label[$label];
  if((int)$variant->get_stock_quantity()!==(int)$expected_stock){exit(8);}
  $existing=(string)$variant->get_regular_price();
  if($existing!=='' && $existing!==(string)$spec['price']){exit(9);}
}
foreach($spec['inventory'] as $label=>$expected_stock){
  $variant=$by_label[$label];
  $variant->set_regular_price((string)$spec['price']);
  $variant->set_sale_price('');
  $variant->set_manage_stock(true);
  $variant->set_stock_status(((int)$expected_stock)>0?'instock':'outofstock');
  $variant->set_status('publish');
  $variant->save();
}
$product=wc_get_product($id);
$product->set_status('publish');
$product->update_meta_data('_aicc_price_status','READY');
$product->save();
WC_Product_Variable::sync($id);
wc_delete_product_transients($id);
$product=wc_get_product($id);
$variants=[];
foreach($product->get_children() as $vid){
  $v=wc_get_product($vid);if(!$v){continue;}
  $label=$v->get_attribute('size');
  if($label===''){$attrs=$v->get_attributes();$label=(string)($attrs['size']??reset($attrs));}
  $variants[]=[
    'id'=>$vid,'label'=>$label,'stock'=>$v->get_stock_quantity(),
    'regular_price'=>$v->get_regular_price(),'available'=>$v->is_in_stock() && $v->get_status()==='publish'
  ];
}
usort($variants,fn($a,$b)=>strcmp($a['label'],$b['label']));
echo wp_json_encode([
 'product_id'=>$id,'status'=>get_post_status($id),'sku'=>$product->get_sku(),
 'price'=>$product->get_price(),'price_status'=>get_post_meta($id,'_aicc_price_status',true),
 'variants'=>$variants
],JSON_UNESCAPED_UNICODE)."\n";
?>'''

def read_spec():
    payload=json.loads((REPO/"brands/agachichi/catalog/dev-upload-products.json").read_text(encoding="utf-8"))
    rows=[row for row in payload.get("products",[]) if row.get("id")==CATALOG_ID]
    if len(rows)!=1:raise RuntimeError("DEV_UPLOAD_PRODUCT_MISSING")
    spec=rows[0]
    if spec.get("price_status")!="READY" or spec.get("price")!=TARGET_PRICE:
        raise RuntimeError("DEV_UPLOAD_PRICE_NOT_READY")
    if spec.get("inventory")!={"S":1,"M":1,"L":1}:raise RuntimeError("DEV_UPLOAD_INVENTORY_INVALID")
    return spec

def verify_media():
    manifest=json.loads((REPO/"brands/agachichi/assets/media/uploads/manifest.json").read_text(encoding="utf-8"))
    rows=[row for row in manifest.get("assets",[]) if row.get("product_id")==CATALOG_ID]
    if len(rows)!=1 or rows[0].get("status")!="READY":raise RuntimeError("DEV_UPLOAD_MEDIA_INVALID")
    image=(REPO/rows[0]["target_path"]).resolve()
    root=(REPO/"brands/agachichi/assets/media/uploads").resolve()
    if not image.is_relative_to(root) or not image.is_file() or image.is_symlink():raise RuntimeError("DEV_UPLOAD_MEDIA_INVALID")
    if hashlib.sha256(image.read_bytes()).hexdigest()!=rows[0].get("sha256"):raise RuntimeError("DEV_UPLOAD_MEDIA_HASH_INVALID")

def main():
    assert_isolation()
    spec=read_spec();verify_media()
    cfg=json.loads((PRIVATE/"runtime.private.json").read_text(encoding="utf-8"))
    if cfg.get("environment")!="DEV":raise RuntimeError("DEV_CONFIGURATION_REQUIRED")
    current=cfg.get("active_products")
    if not isinstance(current,list) or len(current)<5:raise RuntimeError("DEV_ACTIVE_PRODUCTS_REQUIRED")

    payload=base64.b64encode(json.dumps(spec,ensure_ascii=False).encode()).decode()
    result=subprocess.run(DOCKER+["exec","-i",CONTAINER,"php","-d","memory_limit=512M"],
        input=PHP.replace("__PAYLOAD__",payload),capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError("DEV_UPLOAD_PROMOTION_FAILED")
    try:evidence=json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:raise RuntimeError("DEV_UPLOAD_PROMOTION_INVALID") from None
    expected=[("L",1,"300000"),("M",1,"300000"),("S",1,"300000")]
    observed=[(v.get("label"),v.get("stock"),v.get("regular_price")) for v in evidence.get("variants",[])]
    if (evidence.get("product_id")!=36 or evidence.get("status")!="publish"
        or evidence.get("price_status")!="READY" or observed!=expected):
        raise RuntimeError("DEV_UPLOAD_PROMOTION_INVALID")

    binding={
      "demo_id":CATALOG_ID,"product_id":evidence["product_id"],"sku":SKU,
      "category":"OUTER","image_demo_id":CATALOG_ID,
      "variants":[{"id":v["id"],"label":v["label"],"available":bool(v["available"]),"stock":v["stock"]}
                  for v in evidence["variants"]]
    }
    rows=[row for row in current if row.get("demo_id")!=CATALOG_ID and row.get("product_id")!=evidence["product_id"]]
    rows.append(binding)
    cfg["active_products"]=rows
    private_write(PRIVATE/"runtime.private.json",cfg)
    RUNTIME.mkdir(parents=True,exist_ok=True)
    private_write(RUNTIME/"upload-product-promotion-evidence.json",{
      "environment":"DEV","catalog_id":CATALOG_ID,"product_id":evidence["product_id"],
      "price":TARGET_PRICE,"price_status":"READY","status":"publish",
      "inventory":{"S":1,"M":1,"L":1},"active_product_count":len(rows),
      "production_mutation":False
    })
    print(json.dumps({
      "promoted":True,"catalog_id":CATALOG_ID,"product_id":evidence["product_id"],
      "price":TARGET_PRICE,"status":"publish","active_product_count":len(rows),
      "inventory":{"S":1,"M":1,"L":1},"production_mutation":False
    },ensure_ascii=False))

if __name__=="__main__":main()
