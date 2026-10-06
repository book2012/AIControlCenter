"""Read-only plan by default; initialize isolated DEV test stock once, without restocking replay."""
from pathlib import Path
import argparse,base64,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from ops.macos.shopping.dev_order_runtime import assert_isolation
from ops.macos.shopping.dev_order_provision import PRIVATE,private_write
from core.homepage.dev_test_stock import overlay
ROOT=Path(__file__).resolve().parents[3]
PHP=r"""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
add_filter('pre_wp_mail',fn()=>false);
$input=json_decode(base64_decode('__PAYLOAD__'),true);$rows=$input['rows'];$apply=$input['apply'];
if(count($rows)!==17){exit(3);}
global $wpdb;
if($wpdb->get_var("SELECT GET_LOCK('aicc_dev_test_stock',5)")!=='1'){exit(4);}
$wpdb->query('START TRANSACTION');
try{
 $before=wc_get_orders(['limit'=>1,'paginate'=>true])->total;$result=[];
 foreach($rows as $s){
  $p=wc_get_product($s['provider_id']);$sku='aicc-dev-'.$s['id'];
  if(!$p||!$p->is_type('variable')||$p->get_sku()!==$sku||$p->get_meta('_aicc_catalog_id')!==$s['id']||$p->get_status()!=='publish'){throw new Exception('BINDING');}
  if($p->get_meta('_aicc_test_stock_initialized')!=='yes'&&$p->get_meta('_aicc_inventory_pending')!=='yes'){throw new Exception('PENDING_REQUIRED');}
  if(!$apply){$result[]=['demo_id'=>$s['id'],'combinations'=>count($s['inventory']),'already_initialized'=>$p->get_meta('_aicc_test_stock_initialized')==='yes'];continue;}
  $initialized=$p->get_meta('_aicc_test_stock_initialized')==='yes';$variants=[];
  foreach($p->get_children() as $vid){
   $v=wc_get_product($vid);
   if($v->get_meta('_aicc_test_combination')!=='yes'){
    if($v->get_stock_quantity()!==0||!in_array($v->get_status(),['publish','private'],true)){throw new Exception('LEGACY_VARIANT_STATE');}
    if($v->get_status()==='private'&&$v->get_meta('_aicc_test_stock_retired')!=='yes'){throw new Exception('LEGACY_VARIANT_OWNER');}
    $v->update_meta_data('_aicc_test_stock_retired','yes');$v->set_status('private');$v->save();
   }
  }
  foreach($s['color_options'] as $color){foreach($s['size_options'] as $size){
   $key=$color['id'].'--'.strtolower($size);$vsku=$sku.'-'.$key;$vid=wc_get_product_id_by_sku($vsku);$fresh=!$vid;
   if($vid){$v=wc_get_product($vid);if($v->get_parent_id()!==$p->get_id()||$v->get_meta('_aicc_test_combination')!=='yes'||$v->get_attribute('color')!==$color['label']||$v->get_attribute('size')!==$size||!$v->managing_stock()||$v->get_backorders()!=='no'||!is_int($v->get_stock_quantity())||$v->get_stock_quantity()<0||$v->get_stock_quantity()>3){throw new Exception('EXISTING_COMBINATION');}}
   else{if($initialized){throw new Exception('INITIALIZED_VARIANT_MISSING');}$v=new WC_Product_Variation();$v->set_parent_id($p->get_id());$v->set_sku($vsku);$v->set_attributes(['color'=>$color['label'],'size'=>$size]);$v->set_manage_stock(true);$v->set_stock_quantity(3);$v->set_stock_status('instock');$v->set_backorders('no');$v->set_regular_price((string)$s['price']);$v->set_status('publish');$v->update_meta_data('_aicc_test_combination','yes');$vid=$v->save();}
   if($v->get_status()!=='publish'||$v->get_regular_price()!==(string)$s['price']){throw new Exception('VARIANT_PRICE_STATUS');}
   $variants[]=['id'=>$vid,'label'=>$color['label'].' / '.$size,'stock'=>$v->get_stock_quantity(),'available'=>$v->is_in_stock(),'created'=>$fresh];
  }}
  $attrs=[];foreach(['Color'=>array_column($s['color_options'],'label'),'Size'=>$s['size_options']] as $name=>$values){$a=new WC_Product_Attribute();$a->set_name($name);$a->set_options($values);$a->set_visible(true);$a->set_variation(true);$attrs[]=$a;}
  $p->set_attributes($attrs);$p->update_meta_data('_aicc_inventory_pending','no');$p->update_meta_data('_aicc_test_stock_initialized','yes');$p->save();WC_Product_Variable::sync($p->get_id());wc_delete_product_transients($p->get_id());
  $result[]=['demo_id'=>$s['id'],'product_id'=>$p->get_id(),'sku'=>$sku,'category'=>strtoupper($s['category']),'image_demo_id'=>$s['id'],'option_type'=>'color_size','inventory_pending'=>false,'inventory_test'=>true,'variants'=>$variants];
 }
 if($before!==wc_get_orders(['limit'=>1,'paginate'=>true])->total){throw new Exception('ORDER_COUNT_CHANGED');}
 $wpdb->query($apply?'COMMIT':'ROLLBACK');echo wp_json_encode(['products'=>$result,'orders_unchanged'=>true]);
}catch(Throwable $e){$wpdb->query('ROLLBACK');fwrite(STDERR,$e->getMessage());exit(5);}finally{$wpdb->get_var("SELECT RELEASE_LOCK('aicc_dev_test_stock')");}
"""
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply-dev',action='store_true');args=parser.parse_args()
    assert_isolation()
    source=ROOT/'brands/agachichi/catalog/dev-upload-products.json'
    records=json.loads(source.read_text())['products'];rows=[r for r in overlay(records,source) if r.get('inventory_test') is True]
    cfg=json.loads((PRIVATE/'runtime.private.json').read_text())
    if cfg.get('environment')!='DEV' or len(cfg['active_products'])!=24:raise ValueError('DEV_CONFIG_SCOPE')
    for row in rows:
        matches=[v for v in cfg['active_products'] if v['demo_id']==row['id']]
        if len(matches)!=1 or matches[0]['sku']!='aicc-dev-'+row['id']:raise ValueError('DEV_PROVIDER_BINDING')
        row['provider_id']=matches[0]['product_id']
    if args.apply_dev:
        backup=PRIVATE/'runtime-before-test-stock.private.json'
        if not backup.exists():private_write(backup,cfg);os.chmod(backup,0o600)
    payload=base64.b64encode(json.dumps({'apply':args.apply_dev,'rows':rows},ensure_ascii=False).encode()).decode()
    proc=subprocess.run(['docker','--context','colima-aicontrolcenter-commerce','exec','-i','aicc-order-dev-wordpress-1','php'],input=PHP.replace('__PAYLOAD__',payload),capture_output=True,text=True,timeout=180)
    if proc.returncode:raise RuntimeError('DEV_TEST_STOCK_INSPECTION_REQUIRED: '+proc.stderr[:120])
    evidence=json.loads(proc.stdout)
    if args.apply_dev:
        bindings={v['demo_id']:v for v in evidence['products']}
        cfg['active_products']=[bindings.get(v['demo_id'],v) for v in cfg['active_products']]
        path=PRIVATE/'runtime.test-stock-candidate.private.json';private_write(path,cfg);os.chmod(path,0o600)
        private_write(PRIVATE/'test-stock-evidence.private.json',evidence);os.chmod(PRIVATE/'test-stock-evidence.private.json',0o600)
    print(json.dumps({'environment':'DEV','products':len(rows),'combinations':sum(len(r['inventory']) for r in rows),'initial_quantity_per_combination':3,'applied':args.apply_dev,'orders_unchanged':evidence['orders_unchanged'],'prod_mutation':False}))
if __name__=='__main__':main()
