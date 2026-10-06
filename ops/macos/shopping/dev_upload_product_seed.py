"""Seed one user-uploaded product as a non-orderable draft in isolated DEV WooCommerce."""
from pathlib import Path
import base64,json,subprocess,sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from ops.macos.shopping.dev_order_provision import RUNTIME,private_write
from ops.macos.shopping.dev_order_runtime import assert_isolation

REPO=Path(__file__).resolve().parents[3]
CATALOG=REPO/"brands/agachichi/catalog/dev-upload-products.json"
IMAGE_ROOT=REPO/"brands/agachichi/assets/media/uploads"
DOCKER=["docker","--context","colima-aicontrolcenter-commerce"]
CONTAINER="aicc-order-dev-wordpress-1"

PHP=r'''<?php
if (getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev') { exit(2); }
require '/var/www/html/wp-load.php';
require_once ABSPATH.'wp-admin/includes/media.php';
require_once ABSPATH.'wp-admin/includes/file.php';
require_once ABSPATH.'wp-admin/includes/image.php';
$spec=json_decode(base64_decode('__PAYLOAD__'),true);
if(!is_array($spec) || $spec['id']!=='ag-upload-outer-0001' || $spec['price_status']!=='PENDING'){exit(3);}
$sku='aicc-dev-'.$spec['id'];
$id=wc_get_product_id_by_sku($sku);
$created=false;
if($id){
  $product=wc_get_product($id);
  if(!$product || !$product->is_type('variable') || $product->get_sku()!==$sku){exit(4);}
}else{
  $product=new WC_Product_Variable();
  $product->set_sku($sku);
  $created=true;
}
$product->set_name($spec['name']);
$product->set_description($spec['description']);
$product->set_short_description('AI 분류: OUTER · 카멜/브라운 · 벨티드 롱 코트');
$product->set_status('draft');

$term=term_exists('OUTER','product_cat');
if(!$term){$term=wp_insert_term('OUTER','product_cat',['slug'=>'outer']);}
if(is_wp_error($term)){exit(5);}
$term_id=(int)(is_array($term)?$term['term_id']:$term);
$product->set_category_ids([$term_id]);

$tag_ids=[];
foreach($spec['tags'] as $name){
  $t=term_exists($name,'product_tag');
  if(!$t){$t=wp_insert_term($name,'product_tag');}
  if(is_wp_error($t)){exit(6);}
  $tag_ids[]=(int)(is_array($t)?$t['term_id']:$t);
}
$product->set_tag_ids($tag_ids);

$attribute=new WC_Product_Attribute();
$attribute->set_name('Size');
$attribute->set_options(array_keys($spec['inventory']));
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
foreach($spec['inventory'] as $label=>$stock){
  $fresh=false;
  if(isset($by_label[$label])){
    $variant=$by_label[$label];
  }else{
    $variant=new WC_Product_Variation();
    $variant->set_parent_id($id);
    $fresh=true;
  }
  $variant->set_attributes(['size'=>$label]);
  $variant->set_manage_stock(true);
  if($fresh || $variant->get_stock_quantity()===null){$variant->set_stock_quantity((int)$stock);}
  $variant->set_stock_status(((int)$variant->get_stock_quantity())>0?'instock':'outofstock');
  $variant->set_regular_price('');
  $variant->set_sale_price('');
  $variant->set_status('publish');
  $variant->save();
}
WC_Product_Variable::sync($id);
$product=wc_get_product($id);
$product->set_status('draft');
$product->update_meta_data('_aicc_catalog_id',$spec['id']);
$product->update_meta_data('_aicc_source','user_upload');
$product->update_meta_data('_aicc_price_status','PENDING');
$product->update_meta_data('_aicc_ai_classification',wp_json_encode([
  'category'=>'OUTER','color'=>['카멜','브라운'],'tags'=>$spec['tags']
],JSON_UNESCAPED_UNICODE));
if(!$product->get_image_id()){
  $file=['name'=>$spec['id'].'.jpg','tmp_name'=>'/tmp/'.$spec['id'].'.jpg'];
  $attachment=media_handle_sideload($file,$id,$spec['description']);
  if(is_wp_error($attachment)){exit(7);}
  $product->set_image_id((int)$attachment);
}
$product->save();
@unlink('/tmp/'.$spec['id'].'.jpg');

$variants=[];
foreach(wc_get_product($id)->get_children() as $vid){
  $v=wc_get_product($vid);if(!$v){continue;}
  $label=$v->get_attribute('size');
  if($label===''){$attrs=$v->get_attributes();$label=(string)($attrs['size']??reset($attrs));}
  $variants[]=[
    'id'=>$vid,'label'=>$label,'stock'=>$v->get_stock_quantity(),
    'regular_price'=>$v->get_regular_price(),'status'=>$v->get_status()
  ];
}
usort($variants,fn($a,$b)=>strcmp($a['label'],$b['label']));
$tag_names=wp_get_post_terms($id,'product_tag',['fields'=>'names']);
echo wp_json_encode([
  'product_id'=>$id,'status'=>get_post_status($id),'sku'=>$sku,'created'=>$created,
  'image_id'=>wc_get_product($id)->get_image_id(),'categories'=>wp_get_post_terms($id,'product_cat',['fields'=>'names']),
  'tags'=>$tag_names,'variants'=>$variants,'price_status'=>get_post_meta($id,'_aicc_price_status',true)
],JSON_UNESCAPED_UNICODE)."\n";
?>'''

def main():
    assert_isolation()
    payload=json.loads(CATALOG.read_text(encoding="utf-8"))
    rows=payload.get("products",[])
    matches=[r for r in rows if r.get("id")=="ag-upload-outer-0001"]
    if len(matches)!=1:raise RuntimeError("DEV_UPLOAD_PRODUCT_MISSING")
    spec=matches[0]
    if spec.get("price_status")!="PENDING" or spec.get("price")!=0:
        raise RuntimeError("DEV_UPLOAD_PRICE_STATE_INVALID")
    if spec.get("inventory")!={"S":1,"M":1,"L":1}:
        raise RuntimeError("DEV_UPLOAD_INVENTORY_INVALID")
    image=IMAGE_ROOT/(spec["id"]+".jpg")
    if not image.is_file() or image.is_symlink():raise RuntimeError("DEV_UPLOAD_IMAGE_INVALID")
    copied=subprocess.run(DOCKER+["cp",str(image),CONTAINER+":/tmp/"+spec["id"]+".jpg"],
                          capture_output=True,text=True,timeout=30)
    if copied.returncode:raise RuntimeError("DEV_UPLOAD_IMAGE_COPY_FAILED")
    encoded=base64.b64encode(json.dumps(spec,ensure_ascii=False).encode()).decode()
    result=subprocess.run(DOCKER+["exec","-i",CONTAINER,"php","-d","memory_limit=512M"],
                          input=PHP.replace("__PAYLOAD__",encoded),capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError("DEV_UPLOAD_WOO_SEED_FAILED")
    try:evidence=json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:raise RuntimeError("DEV_UPLOAD_WOO_SEED_INVALID") from None
    if evidence.get("status")!="draft" or evidence.get("price_status")!="PENDING" or not evidence.get("image_id"):
        raise RuntimeError("DEV_UPLOAD_WOO_DRAFT_INVALID")
    variants=evidence.get("variants",[])
    if [(v.get("label"),v.get("stock"),v.get("regular_price")) for v in variants] != [("L",1,""),("M",1,""),("S",1,"")]:
        raise RuntimeError("DEV_UPLOAD_WOO_VARIANTS_INVALID")
    private_write(RUNTIME/"upload-product-evidence.json",{
        "environment":"DEV","catalog_id":spec["id"],"product_id":evidence["product_id"],
        "status":"draft","price_status":"PENDING","inventory":{"S":1,"M":1,"L":1},
        "image_attached":True,"production_mutation":False
    })
    print(json.dumps({
        "seeded":True,"catalog_id":spec["id"],"product_id":evidence["product_id"],
        "status":evidence["status"],"inventory":{"S":1,"M":1,"L":1},
        "price_status":"PENDING","image_attached":True,"production_mutation":False
    },ensure_ascii=False))

if __name__=="__main__":main()
