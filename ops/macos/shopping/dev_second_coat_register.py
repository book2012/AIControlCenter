"""Register the second reviewed coat in isolated DEV only; preserve existing stock on replay."""
from pathlib import Path
import base64,hashlib,json,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from ops.macos.shopping.dev_order_provision import PRIVATE,RUNTIME,private_write
from ops.macos.shopping.dev_order_runtime import assert_isolation
REPO=Path(__file__).resolve().parents[3]
ID="ag-upload-outer-0002"
def read_spec():
    rows=json.loads((REPO/"brands/agachichi/catalog/dev-upload-products.json").read_text())["products"]
    matches=[r for r in rows if r["id"]==ID]
    if len(matches)!=1:raise ValueError("SECOND_COAT_SPEC_REQUIRED")
    spec=matches[0]
    if spec["source"]!="user_upload" or spec["price_status"]!="READY" or spec["price"]!=450000 or spec["inventory"]!={"M":1,"L":1} or spec["category"]!="outer" or spec["currency"]!="KRW":
        raise ValueError("SECOND_COAT_SPEC_INVALID")
    manifest=json.loads((REPO/"brands/agachichi/assets/media/uploads/manifest.json").read_text())
    entries=[r for r in manifest["assets"] if r["product_id"]==ID and r["status"]=="READY"]
    if len(entries)!=1:raise ValueError("SECOND_COAT_MEDIA_REQUIRED")
    image=REPO/"brands/agachichi/assets/media/uploads"/(ID+".jpg")
    if image.is_symlink() or not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest()!=entries[0]["sha256"]:
        raise ValueError("SECOND_COAT_MEDIA_INVALID")
    return spec,image,entries[0]["sha256"]
PHP=r"""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
require_once ABSPATH.'wp-admin/includes/media.php';
require_once ABSPATH.'wp-admin/includes/file.php';
require_once ABSPATH.'wp-admin/includes/image.php';
add_filter('pre_wp_mail',fn()=>false);
$s=json_decode(base64_decode('__PAYLOAD__'),true);
if($s['id']!=='ag-upload-outer-0002'||$s['price']!==450000||$s['inventory']!==['M'=>1,'L'=>1]){exit(3);}
global $wpdb;
if($wpdb->get_var("SELECT GET_LOCK('aicc_dev_second_coat',5)")!=='1'){exit(4);}
try{
 $sku='aicc-dev-'.$s['id'];$id=wc_get_product_id_by_sku($sku);$fresh=!$id;
 if($id){
  $p=wc_get_product($id);
  if(!$p||!$p->is_type('variable')||$p->get_meta('_aicc_catalog_id')!==$s['id']||$p->get_meta('_aicc_image_sha256')!==$s['sha256']||$p->get_status()!=='publish'){throw new Exception('EXISTING_BINDING');}
 }else{
  $p=new WC_Product_Variable();$p->set_sku($sku);$p->set_name($s['name']);$p->set_description($s['description']);$p->set_status('draft');
  $term=term_exists('OUTER','product_cat');if(!$term){$term=wp_insert_term('OUTER','product_cat',['slug'=>'outer']);}
  if(is_wp_error($term)){throw new Exception('CATEGORY');}
  $p->set_category_ids([(int)(is_array($term)?$term['term_id']:$term)]);
  $tags=[];foreach($s['tags'] as $name){$t=term_exists($name,'product_tag');if(!$t){$t=wp_insert_term($name,'product_tag');}if(is_wp_error($t)){throw new Exception('TAG');}$tags[]=(int)(is_array($t)?$t['term_id']:$t);}
  $p->set_tag_ids($tags);
  $a=new WC_Product_Attribute();$a->set_name('Size');$a->set_options(['M','L']);$a->set_visible(true);$a->set_variation(true);$p->set_attributes([$a]);$id=$p->save();
  $p->update_meta_data('_aicc_catalog_id',$s['id']);$p->update_meta_data('_aicc_image_sha256',$s['sha256']);$p->update_meta_data('_aicc_source','user_upload');$p->update_meta_data('_aicc_price_status','READY');$p->save();
  foreach($s['inventory'] as $label=>$stock){$v=new WC_Product_Variation();$v->set_parent_id($id);$v->set_attributes(['size'=>$label]);$v->set_manage_stock(true);$v->set_stock_quantity($stock);$v->set_backorders('no');$v->set_stock_status('instock');$v->set_regular_price('450000');$v->set_status('publish');$v->save();}
  $attachment=media_handle_sideload(['name'=>$s['id'].'.jpg','tmp_name'=>'/tmp/'.$s['id'].'.jpg'],$id,$s['name']);
  if(is_wp_error($attachment)){throw new Exception('MEDIA');}
  $p->set_image_id((int)$attachment);$p->set_status('publish');$p->save();WC_Product_Variable::sync($id);wc_delete_product_transients($id);
 }
 $p=wc_get_product($id);$variants=[];
 foreach($p->get_children() as $vid){$v=wc_get_product($vid);$label=$v->get_attribute('size');if(!in_array($label,['M','L'],true)||$v->get_regular_price()!=='450000'||!$v->managing_stock()||$v->get_stock_quantity()<0||$v->get_stock_quantity()>1){throw new Exception('VARIANT_BINDING');}$variants[]=['id'=>$vid,'label'=>$label,'stock'=>$v->get_stock_quantity(),'available'=>$v->is_in_stock(),'price'=>$v->get_regular_price()];}
 if(count($variants)!==2||!$p->get_image_id()||hash_file('sha256',get_attached_file($p->get_image_id()))!==$s['sha256']){throw new Exception('RECEIPT');}
 echo wp_json_encode(['product_id'=>$id,'created'=>$fresh,'sku'=>$sku,'status'=>$p->get_status(),'image_id'=>$p->get_image_id(),'variants'=>$variants]);
}catch(Throwable $e){exit(5);}finally{$wpdb->get_var("SELECT RELEASE_LOCK('aicc_dev_second_coat')");}
"""
def main():
    assert_isolation();spec,image,digest=read_spec()
    cfg=json.loads((PRIVATE/"runtime.private.json").read_text())
    if cfg.get("environment")!="DEV" or len(cfg.get("active_products",[]))<6:raise ValueError("DEV_MAPPING_REQUIRED")
    command=["docker","--context","colima-aicontrolcenter-commerce"]
    subprocess.run(command+["cp",str(image),"aicc-order-dev-wordpress-1:/tmp/"+ID+".jpg"],capture_output=True,check=True,timeout=20)
    payload=base64.b64encode(json.dumps({**spec,"sha256":digest},ensure_ascii=False).encode()).decode()
    r=subprocess.run(command+["exec","-i","aicc-order-dev-wordpress-1","php","-d","memory_limit=512M"],input=PHP.replace("__PAYLOAD__",payload),capture_output=True,text=True,timeout=90)
    if r.returncode:raise RuntimeError("SECOND_COAT_REGISTRATION_REQUIRES_INSPECTION")
    v=json.loads(r.stdout);assert v["status"]=="publish" and len(v["variants"])==2
    existing=[x for x in cfg["active_products"] if x["demo_id"]==ID or x["product_id"]==v["product_id"]]
    if existing and (len(existing)!=1 or existing[0]["demo_id"]!=ID or existing[0]["product_id"]!=v["product_id"]):raise ValueError("DEV_MAPPING_CONFLICT")
    binding={"demo_id":ID,"product_id":v["product_id"],"sku":v["sku"],"category":"OUTER","image_demo_id":ID,"variants":[{k:x[k] for k in ("id","label","available","stock")} for x in v["variants"]]}
    cfg["active_products"]=[x for x in cfg["active_products"] if x["demo_id"]!=ID]+[binding]
    private_write(PRIVATE/"runtime.private.json",cfg)
    evidence={"environment":"DEV","catalog_id":ID,"price":450000,"inventory":{x["label"]:x["stock"] for x in v["variants"]},"prod_mutation":False,**v}
    private_write(RUNTIME/"second-coat-evidence.json",evidence)
    print(json.dumps(evidence,ensure_ascii=False))
if __name__=="__main__":main()
