"""Register reviewed photo batch in isolated DEV. Default is read-only; stage bindings for release activation."""
from pathlib import Path
import argparse,base64,hashlib,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from ops.macos.shopping.dev_order_provision import PRIVATE,RUNTIME,private_write
from ops.macos.shopping.dev_order_runtime import assert_isolation
REPO=Path(__file__).resolve().parents[3]
def read_specs():
    document=json.loads((REPO/'brands/agachichi/catalog/dev-upload-products.json').read_text())
    rows=[v for v in document['products'] if v.get('inventory_pending') is True]
    manifest=json.loads((REPO/'brands/agachichi/assets/media/uploads/manifest.json').read_text())
    if document['environment']!='DEV' or manifest['environment']!='DEV' or len(rows)!=17:raise ValueError('REVIEWED_DEV_BATCH_REQUIRED')
    result=[]
    for row in rows:
        if row['source']!='user_upload' or row['option_type']!='color' or row['price_status']!='READY' or type(row['price']) is not int or row['price']<=0 or row['price_basis']!='user_authorized_temporary' or row['currency']!='KRW' or any(type(n) is not int or n!=0 for n in row['inventory'].values()):raise ValueError('PENDING_STOCK_BATCH_REQUIRED')
        options=row['color_options']
        if len({v['id'] for v in options})!=len(options) or set(row['inventory'])!={v['id'] for v in options}:raise ValueError('COLOR_BINDING')
        matches=[v for v in manifest['assets'] if v['product_id']==row['id'] and v['status']=='READY']
        image=REPO/'brands/agachichi/assets/media/uploads'/(row['id']+'.jpg')
        if len(matches)!=1 or image.is_symlink() or not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest()!=matches[0]['sha256']:raise ValueError('BATCH_MEDIA_REQUIRED')
        result.append({**row,'sha256':matches[0]['sha256']})
    return result
PHP=r"""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
require_once ABSPATH.'wp-admin/includes/media.php';require_once ABSPATH.'wp-admin/includes/file.php';require_once ABSPATH.'wp-admin/includes/image.php';
add_filter('pre_wp_mail',fn()=>false);
$rows=json_decode(base64_decode('__PAYLOAD__'),true);if(count($rows)!==17){exit(3);}
global $wpdb;if($wpdb->get_var("SELECT GET_LOCK('aicc_dev_upload_batch',5)")!=='1'){exit(4);}
try{
 $result=[];$before=$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='shop_order'");
 foreach($rows as $s){
  if($s['inventory_pending']!==true||$s['option_type']!=='color'||$s['currency']!=='KRW'||$s['price_basis']!=='user_authorized_temporary'||!is_int($s['price'])||$s['price']<=0||!preg_match('/^ag-upload-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/',$s['id'])){throw new Exception('SPEC');}
  foreach($s['inventory'] as $qty){if($qty!==0){throw new Exception('STOCK');}}
  $sku='aicc-dev-'.$s['id'];$id=wc_get_product_id_by_sku($sku);$fresh=!$id;
  if($id){
   $p=wc_get_product($id);
   if(!$p||!$p->is_type('variable')||$p->get_meta('_aicc_catalog_id')!==$s['id']||$p->get_meta('_aicc_image_sha256')!==$s['sha256']||$p->get_status()!=='publish'||$p->get_meta('_aicc_inventory_pending')!=='yes'){throw new Exception('EXISTING_BINDING');}
  }else{
   $p=new WC_Product_Variable();$p->set_sku($sku);$p->set_name($s['name']);$p->set_description($s['description']);$p->set_status('draft');
   $category=strtoupper($s['category']);$term=term_exists($category,'product_cat');if(!$term){$term=wp_insert_term($category,'product_cat',['slug'=>$s['category']]);}if(is_wp_error($term)){throw new Exception('CATEGORY');}
   $p->set_category_ids([(int)(is_array($term)?$term['term_id']:$term)]);
   $tags=[];foreach($s['tags'] as $name){$term=term_exists($name,'product_tag');if(!$term){$term=wp_insert_term($name,'product_tag');}if(is_wp_error($term)){throw new Exception('TAG');}$tags[]=(int)(is_array($term)?$term['term_id']:$term);}$p->set_tag_ids($tags);
   $a=new WC_Product_Attribute();$a->set_name('Color');$a->set_options(array_column($s['color_options'],'label'));$a->set_visible(true);$a->set_variation(true);$p->set_attributes([$a]);
   foreach(['_aicc_catalog_id'=>$s['id'],'_aicc_image_sha256'=>$s['sha256'],'_aicc_source'=>'user_upload','_aicc_price_status'=>'READY','_aicc_inventory_pending'=>'yes','_aicc_price_basis'=>'user_authorized_temporary'] as $k=>$v){$p->update_meta_data($k,$v);}
   $id=$p->save();
   foreach($s['color_options'] as $option){$v=new WC_Product_Variation();$v->set_sku($sku.'-'.$option['id']);$v->set_parent_id($id);$v->set_attributes(['color'=>$option['label']]);$v->set_manage_stock(true);$v->set_stock_quantity(0);$v->set_backorders('no');$v->set_stock_status('outofstock');$v->set_regular_price((string)$s['price']);$v->set_status('publish');$v->save();}
   $attachment=media_handle_sideload(['name'=>$s['id'].'.jpg','tmp_name'=>'/tmp/'.$s['id'].'.jpg'],$id,$s['name']);if(is_wp_error($attachment)){throw new Exception('MEDIA');}
   $p->set_image_id((int)$attachment);$p->set_status('publish');$p->save();WC_Product_Variable::sync($id);wc_delete_product_transients($id);
  }
  $p=wc_get_product($id);$variants=[];$labels=[];
  foreach($p->get_children() as $vid){$v=wc_get_product($vid);$label=$v->get_attribute('color');if(!in_array($label,array_column($s['color_options'],'label'),true)||$v->get_regular_price()!==(string)$s['price']||!$v->managing_stock()||$v->get_stock_quantity()!==0||$v->is_in_stock()||$v->get_backorders()!=='no'){throw new Exception('VARIANT_BINDING');}$labels[]=$label;$variants[]=['id'=>$vid,'label'=>$label,'stock'=>0,'available'=>false,'price'=>$v->get_regular_price()];}
  if(count($variants)!==count($s['color_options'])||count(array_unique($labels))!==count($labels)||!$p->get_image_id()||hash_file('sha256',get_attached_file($p->get_image_id()))!==$s['sha256']){throw new Exception('RECEIPT');}
  $result[]=['demo_id'=>$s['id'],'product_id'=>$id,'created'=>$fresh,'sku'=>$sku,'category'=>strtoupper($s['category']),'image_demo_id'=>$s['id'],'option_type'=>'color','inventory_pending'=>true,'variants'=>$variants];
 }
 if($before!==$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type='shop_order'")){throw new Exception('ORDER_COUNT_CHANGED');}
 echo wp_json_encode($result);
}catch(Throwable $e){fwrite(STDERR,$e->getMessage());exit(5);}finally{$wpdb->get_var("SELECT RELEASE_LOCK('aicc_dev_upload_batch')");}
"""
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply-dev',action='store_true');args=parser.parse_args()
    assert_isolation();rows=read_specs();cfg=json.loads((PRIVATE/'runtime.private.json').read_text())
    if cfg.get('environment')!='DEV' or len(cfg.get('active_products',[]))<7:raise ValueError('DEV_MAPPING_REQUIRED')
    if not args.apply_dev:
        print(json.dumps({'environment':'DEV','planned_products':len(rows),'prices':'temporary','stock':'pending zero','mutation':False}));return
    cmd=['docker','--context','colima-aicontrolcenter-commerce']
    for row in rows:
        subprocess.run(cmd+['cp',str(REPO/'brands/agachichi/assets/media/uploads'/(row['id']+'.jpg')),'aicc-order-dev-wordpress-1:/tmp/'+row['id']+'.jpg'],capture_output=True,check=True,timeout=20)
    payload=base64.b64encode(json.dumps(rows,ensure_ascii=False).encode()).decode()
    proc=subprocess.run(cmd+['exec','-i','aicc-order-dev-wordpress-1','php','-d','memory_limit=512M'],input=PHP.replace('__PAYLOAD__',payload),capture_output=True,text=True,timeout=180)
    if proc.returncode:raise RuntimeError('DEV_BATCH_REGISTRATION_REQUIRES_INSPECTION: '+proc.stderr[:100])
    result=json.loads(proc.stdout)
    for binding in result:
        existing=[v for v in cfg['active_products'] if v['demo_id']==binding['demo_id'] or v['product_id']==binding['product_id']]
        if existing and (len(existing)!=1 or existing[0]['demo_id']!=binding['demo_id'] or existing[0]['product_id']!=binding['product_id']):raise ValueError('MAPPING_CONFLICT')
        cfg['active_products']=[v for v in cfg['active_products'] if v['demo_id']!=binding['demo_id']]+[{k:v for k,v in binding.items() if k!='created'}]
    candidate=PRIVATE/'runtime.batch-candidate.private.json';private_write(candidate,cfg);os.chmod(candidate,0o600)
    private_write(RUNTIME/'upload-batch-evidence.json',{'environment':'DEV','products':result,'prod_mutation':False});os.chmod(RUNTIME/'upload-batch-evidence.json',0o600)
    print(json.dumps({'environment':'DEV','registered':len(result),'created':sum(v['created'] for v in result),'binding_staged':True,'prod_mutation':False}))
if __name__=='__main__':main()
