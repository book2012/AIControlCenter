"""Private DEV operator UX and atomic Woo stock confirmation. No PROD composition."""
import base64, hashlib, json, re, sqlite3, subprocess
from pathlib import Path
from core.shopping.order_core.guest_checkout import fingerprint
from core.shopping.order_core.telegram import OrderTelegramIntegration

from core.shopping.guest_operator import local_phone,GuestOperatorAdapter as DevOperatorAdapter

class DevStockConfirmation:
    def __init__(self,*,store):self.store=store
    def __call__(self,key,result):
        # Caller is the ledger's serialized authorized confirmation transaction.
        try:
            tag=hashlib.sha256(("aicc-order:"+key).encode()).hexdigest()
            draft=self.store.by_provider_tag(tag,allow_expired=True)
            if draft["state"]!="CONFIRMED":return False
            expected={"order_id":result.snapshot.provider_order_id,"tag":tag,"digest":draft["digest"],
                "items":[{"product":int(v["product_id"]),"variation":int(v["variation_id"]),"quantity":v["quantity"]} for v in draft["body"]["line_items"]]}
            return self.apply(expected)["outcome"]=="STOCK_CONFIRMED"
        except Exception:return False
    def apply(self,expected):
        from ops.macos.shopping.dev_order_runtime import assert_isolation
        assert_isolation()
        encoded=base64.b64encode(json.dumps(expected).encode()).decode()
        script=STOCK_PHP.replace("__PAYLOAD__",encoded)
        r=subprocess.run(["docker","--context","colima-aicontrolcenter-commerce","exec","-i","aicc-order-dev-wordpress-1","php"],
            input=script,capture_output=True,text=True,timeout=25)
        if r.returncode:raise RuntimeError("DEV_STOCK_CONFIRMATION_BLOCKED")
        value=json.loads(r.stdout)
        if value.get("outcome")!="STOCK_CONFIRMED":raise RuntimeError("DEV_STOCK_RECEIPT_INVALID")
        return value

STOCK_PHP="""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
add_filter('pre_wp_mail',fn()=>false);
$cfg=json_decode(base64_decode('__PAYLOAD__'),true);
global $wpdb;
if($wpdb->get_var("SELECT GET_LOCK('aicc_dev_stock_confirmation',5)")!=='1'){exit(3);}
try {
 $bad=$wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND engine IS NOT NULL AND engine<>'InnoDB'",DB_NAME));
 if((int)$bad!==0){throw new Exception('ENGINE');}
 $wpdb->query('START TRANSACTION');
 $order=wc_get_order($cfg['order_id']);
 if(!$order || $order->get_meta('_aicc_order_operation')!==$cfg['tag'] || $order->get_meta('_aicc_delivery_digest')!==$cfg['digest']){throw new Exception('BINDING');}
 if(!in_array($order->get_status(),['pending','on-hold'],true)){throw new Exception('STATUS');}
 $items=array_values($order->get_items());$actual=[];$needs=[];
 foreach($items as $item){
  $actual[]=['product'=>$item->get_product_id(),'variation'=>$item->get_variation_id(),'quantity'=>$item->get_quantity()];
  $p=$item->get_product();$qty=$item->get_quantity();$reduced=$item->get_meta('_reduced_stock',true);
  if(!$p || !$p->managing_stock() || $p->backorders_allowed()){throw new Exception('STOCK_POLICY');}
  if($reduced!=='' && (int)$reduced!==$qty){throw new Exception('REDUCED_BINDING');}
  if($reduced===''){
   $id=$p->get_stock_managed_by_id();$needs[$id]=($needs[$id]??0)+$qty;
  }
 }
 if($actual!=$cfg['items']){throw new Exception('ITEM_BINDING');}
 foreach($needs as $id=>$qty){$p=wc_get_product($id);if(!$p || $p->get_stock_quantity()<$qty){throw new Exception('INSUFFICIENT');}}
 if(get_option('woocommerce_manage_stock')!=='yes'){throw new Exception('MANAGEMENT_DISABLED');}
 wc_reduce_stock_levels($order);
 foreach($items as $item){$item->read_meta_data(true);if((int)$item->get_meta('_reduced_stock',true)!==$item->get_quantity()){throw new Exception('REDUCTION_UNVERIFIED');}}
 $order->get_data_store()->set_stock_reduced($order->get_id(),true);
 if($order->get_status()==='pending'){$order->update_status('on-hold','DEV operator confirmed; stock accounted; no payment or shipment.');}
 $order->update_meta_data('_aicc_stock_confirmation',$cfg['tag']);$order->save();
 $wpdb->query('COMMIT');
 $stocks=[];foreach($items as $item){$p=wc_get_product($item->get_variation_id()?:$item->get_product_id());$stocks[]=['variation'=>$item->get_variation_id(),'quantity'=>$p->get_stock_quantity(),'stock_status'=>$p->get_stock_status()];}
 echo json_encode(['outcome'=>'STOCK_CONFIRMED','order_id'=>$order->get_id(),'stocks'=>$stocks]);
} catch(Throwable $e) {$wpdb->query('ROLLBACK');exit(4);}
finally {$wpdb->get_var("SELECT RELEASE_LOCK('aicc_dev_stock_confirmation')");}
"""
