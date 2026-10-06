"""Idempotently seed five orderable products into isolated DEV WooCommerce only."""
from pathlib import Path
import base64,json,subprocess,sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from ops.macos.shopping.dev_order_provision import PRIVATE,RUNTIME,private_write
from ops.macos.shopping.dev_order_runtime import assert_isolation

REPO=Path(__file__).resolve().parents[3]
DOCKER=["docker","--context","colima-aicontrolcenter-commerce"]
CONTAINER="aicc-order-dev-wordpress-1"

PHP=r'''<?php
if (getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev') { exit(2); }
require '/var/www/html/wp-load.php';
if (!class_exists('WooCommerce')) { exit(3); }
$products=json_decode(base64_decode('__PAYLOAD__'),true);
if (!is_array($products) || count($products)!==5) { exit(4); }
$out=[];
foreach($products as $spec){
  $demo=$spec['demo_id'];
  if(!preg_match('/^oc-demo-(top|bottom|outer|dress|bag)-0001$/',$demo)){exit(5);}
  $sku='aicc-dev-'.$demo;
  $id=wc_get_product_id_by_sku($sku);
  $created=false;
  if($id){
    $product=wc_get_product($id);
    if(!$product || !$product->is_type('variable') || $product->get_sku()!==$sku){exit(6);}
  } else {
    $product=new WC_Product_Variable();
    $product->set_sku($sku);
    $created=true;
  }
  $product->set_name($spec['name']);
  $product->set_description($spec['description']);
  $product->set_status('publish');
  $attribute=new WC_Product_Attribute();
  $attribute->set_name('Size');
  $attribute->set_options(array_map(fn($v)=>$v['label'],$spec['options']));
  $attribute->set_visible(true);
  $attribute->set_variation(true);
  $product->set_attributes([$attribute]);
  $id=$product->save();

  $by_label=[];
  foreach($product->get_children() as $vid){
    $v=wc_get_product($vid);
    if(!$v){continue;}
    $label=$v->get_attribute('size');
    if($label===''){
      $attrs=$v->get_attributes();
      $label=(string)($attrs['size']??reset($attrs));
    }
    if($label!==''){$by_label[$label]=$v;}
  }
  foreach($spec['options'] as $option){
    $label=$option['label'];
    $fresh=false;
    if(isset($by_label[$label])){
      $variant=$by_label[$label];
    } else {
      $variant=new WC_Product_Variation();
      $variant->set_parent_id($id);
      $fresh=true;
    }
    $variant->set_attributes(['size'=>$label]);
    $variant->set_regular_price($spec['price']);
    $variant->set_manage_stock(true);
    if($fresh || $variant->get_stock_quantity()===null){
      $variant->set_stock_quantity((int)$option['stock']);
    }
    $qty=(int)$variant->get_stock_quantity();
    $variant->set_stock_status($qty>0?'instock':'outofstock');
    $variant->set_status('publish');
    $variant->save();
  }
  WC_Product_Variable::sync($id);
  wc_delete_product_transients($id);
  $variants=[];
  foreach(wc_get_product($id)->get_children() as $vid){
    $v=wc_get_product($vid); if(!$v){continue;}
    $label=$v->get_attribute('size');
    if($label===''){$attrs=$v->get_attributes();$label=(string)($attrs['size']??reset($attrs));}
    $variants[]=['id'=>$vid,'label'=>$label,'available'=>$v->is_in_stock(),'stock'=>$v->get_stock_quantity()];
  }
  usort($variants,fn($a,$b)=>strcmp($a['label'],$b['label']));
  $out[]=['demo_id'=>$demo,'product_id'=>$id,'sku'=>$sku,'category'=>$spec['category'],'price'=>$spec['price'],'created'=>$created,'variants'=>$variants];
}
echo json_encode(['products'=>$out],JSON_UNESCAPED_UNICODE)."\n";
?>'''

def main():
    assert_isolation()
    spec=json.loads((REPO/"deploy/shopping/dev-order/test-products.json").read_text())
    payload=base64.b64encode(json.dumps(spec,ensure_ascii=False).encode()).decode()
    code=PHP.replace("__PAYLOAD__",payload)
    result=subprocess.run(DOCKER+["exec","-i",CONTAINER,"php","-d","memory_limit=512M"],
                          input=code,capture_output=True,text=True,timeout=120)
    if result.returncode:
        raise RuntimeError("DEV_MULTI_PRODUCT_SEED_FAILED")
    try:
        raw=json.loads(result.stdout[result.stdout.rfind("\n",0,len(result.stdout)-1)+1:] or result.stdout)
    except Exception:
        try: raw=json.loads(result.stdout[result.stdout.index("{"):])
        except Exception: raise RuntimeError("DEV_MULTI_PRODUCT_SEED_INVALID") from None
    products=raw.get("products")
    if not isinstance(products,list) or len(products)!=len(spec):
        raise RuntimeError("DEV_MULTI_PRODUCT_SEED_INVALID")
    expected={v["demo_id"]:v for v in spec}
    normalized=[]
    for item in products:
        source=expected.get(item.get("demo_id"))
        if not source or not isinstance(item.get("product_id"),int) or item["product_id"]<=0:
            raise RuntimeError("DEV_MULTI_PRODUCT_SEED_INVALID")
        expected_labels={v["label"] for v in source["options"]}
        labels={v.get("label") for v in item.get("variants",[])}
        if labels!=expected_labels:
            raise RuntimeError("DEV_MULTI_PRODUCT_VARIANTS_INVALID")
        normalized.append({
            "demo_id":item["demo_id"],"product_id":item["product_id"],"sku":item["sku"],
            "category":source["category"],"image_demo_id":item["demo_id"],
            "variants":[{"id":v["id"],"label":v["label"],"available":bool(v["available"]),"stock":v["stock"]} for v in item["variants"]],
        })
    cfg=json.loads((PRIVATE/"runtime.private.json").read_text())
    if cfg.get("environment")!="DEV":raise RuntimeError("DEV_CONFIGURATION_REQUIRED")
    cfg["active_products"]=normalized
    top=next(v for v in normalized if v["demo_id"]=="oc-demo-top-0001")
    cfg["provider_product_id"]=top["product_id"]
    cfg["variants"]=[{"id":v["id"],"label":v["label"],"available":v["available"]} for v in top["variants"]]
    private_write(PRIVATE/"runtime.private.json",cfg)
    RUNTIME.mkdir(parents=True,exist_ok=True)
    evidence={"environment":"DEV","active_products":normalized,"product_count":len(normalized),
              "container":CONTAINER,"production_mutation":False}
    private_write(RUNTIME/"multi-product-evidence.json",evidence)
    print(json.dumps({"seeded":True,"product_count":len(normalized),
                      "products":[{"demo_id":v["demo_id"],"product_id":v["product_id"],"variants":v["variants"]} for v in normalized],
                      "production_mutation":False},ensure_ascii=False))

if __name__=="__main__":
    main()
