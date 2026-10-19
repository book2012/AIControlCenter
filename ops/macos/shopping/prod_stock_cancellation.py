"""WooCommerce cancellation bound to the production commerce identity."""
import base64,hashlib,json,subprocess
from ops.macos.shopping.prod_woo_port import assert_production,DOCKER

class ProductionStockCancellation:
    """Bound production Woo cancellation primitive; caller must authorize cancellation.

    This is not return approval, payment refund or a public customer endpoint.
    """
    def __init__(self,*,store):self.store=store
    @staticmethod
    def expected(row,draft):
        if draft["state"]!="CONFIRMED":raise ValueError("ORDER_NOT_CONFIRMED")
        return {"order_id":row["provider_order_id"],"tag":hashlib.sha256(("aicc-order:"+row["operation_key"]).encode()).hexdigest(),
            "digest":draft["digest"],"items":[{"product":int(v["product_id"]),"variation":int(v["variation_id"]),"quantity":v["quantity"]} for v in draft["body"]["line_items"]]}
    def __call__(self,row,draft):return self.apply(self.expected(row,draft))
    def reconcile(self,row,draft):
        assert_production();expected=self.expected(row,draft)
        encoded=base64.b64encode(json.dumps(expected).encode()).decode()
        code=CANCEL_RECONCILE_PHP.replace("__PAYLOAD__",encoded)
        r=subprocess.run([DOCKER,"--context","colima-aicontrolcenter-commerce","exec","-i","shopping-wordpress","php"],input=code,capture_output=True,text=True,timeout=25)
        if r.returncode:raise ValueError("CANCELLATION_RECONCILIATION_REQUIRED")
        value=json.loads(r.stdout)
        if value.get("outcome")!="STOCK_CANCELLED" or value.get("order_id")!=expected["order_id"]:raise ValueError("CANCELLATION_RECONCILIATION_REQUIRED")
        return value
    def apply(self,expected):
        assert_production()
        encoded=base64.b64encode(json.dumps(expected).encode()).decode()
        r=subprocess.run([DOCKER,"--context","colima-aicontrolcenter-commerce","exec","-i","shopping-wordpress","php"],
            input=CANCEL_STOCK_PHP.replace("__PAYLOAD__",encoded),capture_output=True,text=True,timeout=25)
        if r.returncode:raise RuntimeError("PROD_STOCK_CANCELLATION_BLOCKED")
        value=json.loads(r.stdout)
        if value.get("outcome")!="STOCK_CANCELLED" or value.get("order_id")!=expected["order_id"]:
            raise RuntimeError("PROD_STOCK_CANCELLATION_RECEIPT_INVALID")
        return value

CANCEL_STOCK_PHP="""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_shopping'){exit(2);}
require '/var/www/html/wp-load.php';
add_filter('pre_wp_mail',fn()=>false);
$cfg=json_decode(base64_decode('__PAYLOAD__'),true);global $wpdb;
if($wpdb->get_var("SELECT GET_LOCK('aicc_prod_stock_cancellation',5)")!=='1'){exit(3);}
try {
 $bad=$wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND engine IS NOT NULL AND engine<>'InnoDB'",DB_NAME));
 if((int)$bad!==0){throw new Exception('ENGINE');}
 $wpdb->query('START TRANSACTION');$order=wc_get_order($cfg['order_id']);
 if(!$order || $order->get_meta('_aicc_order_operation')!==$cfg['tag'] || $order->get_meta('_aicc_delivery_digest')!==$cfg['digest']){throw new Exception('BINDING');}
 $items=array_values($order->get_items());$actual=[];
 foreach($items as $item){$actual[]=['product'=>$item->get_product_id(),'variation'=>$item->get_variation_id(),'quantity'=>$item->get_quantity()];}
 if($actual!=$cfg['items']){throw new Exception('ITEM_BINDING');}
 if($order->get_meta('_aicc_stock_return')!==''){throw new Exception('RETURN_ALREADY_RESTORED');}
 $receipt=$order->get_meta('_aicc_stock_cancellation');
 if($receipt!=='' && $receipt!==$cfg['tag']){throw new Exception('RECEIPT_BINDING');}
 if($receipt===''){
  $status=$order->get_status();$stock_reduced=(bool)$order->get_data_store()->get_stock_reduced($order->get_id());
  $confirmed=$order->get_meta('_aicc_stock_confirmation')===$cfg['tag'];
  if(!$confirmed){
   // A waiting-review order may be cancelled only while Woo has not reduced stock.
   if($status!=='pending' || $stock_reduced){throw new Exception('PENDING_ORDER_STATE');}
   foreach($items as $item){if($item->get_meta('_reduced_stock',true)!==''){throw new Exception('UNCONFIRMED_REDUCED_STOCK');}}
  } else {
   if(!in_array($status,['pending','on-hold'],true) || !$stock_reduced){throw new Exception('CONFIRMED_ORDER_STATE');}
   foreach($items as $item){if((int)$item->get_meta('_reduced_stock',true)!==$item->get_quantity()){throw new Exception('REDUCED_BINDING');}}
   wc_maybe_increase_stock_levels($order->get_id());
   foreach($items as $item){$item->read_meta_data(true);if($item->get_meta('_reduced_stock',true)!==''){throw new Exception('RESTORATION_UNVERIFIED');}}
   if($order->get_data_store()->get_stock_reduced($order->get_id())){throw new Exception('RESTORATION_FLAG');}
  }
  $order->update_status('cancelled','PROD cancellation; verified stock handling; no automatic payment refund.');
  $order->update_meta_data('_aicc_stock_cancellation',$cfg['tag']);$order->save();
 } elseif($order->get_status()!=='cancelled'){throw new Exception('RECEIPT_STATUS');}
 $wpdb->query('COMMIT');$stocks=[];
 foreach($items as $item){$p=$item->get_product();$stocks[]=['variation'=>$item->get_variation_id(),'quantity'=>$p->get_stock_quantity()];}
 echo json_encode(['outcome'=>'STOCK_CANCELLED','order_id'=>$order->get_id(),'stocks'=>$stocks]);
} catch(Throwable $e){$wpdb->query('ROLLBACK');exit(4);}
finally{$wpdb->get_var("SELECT RELEASE_LOCK('aicc_prod_stock_cancellation')");}
"""

CANCEL_RECONCILE_PHP="""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_shopping'){exit(2);}
require '/var/www/html/wp-load.php';
$cfg=json_decode(base64_decode('__PAYLOAD__'),true);$order=wc_get_order($cfg['order_id']);
if(!$order || $order->get_meta('_aicc_order_operation')!==$cfg['tag'] || $order->get_meta('_aicc_delivery_digest')!==$cfg['digest'] || $order->get_meta('_aicc_stock_cancellation')!==$cfg['tag'] || $order->get_status()!=='cancelled'){exit(3);}
$actual=[];foreach($order->get_items() as $item){
 $actual[]=['product'=>$item->get_product_id(),'variation'=>$item->get_variation_id(),'quantity'=>$item->get_quantity()];
 if($item->get_meta('_reduced_stock',true)!==''){exit(4);}
}
if($actual!=$cfg['items'] || $order->get_data_store()->get_stock_reduced($order->get_id())){exit(5);}
echo json_encode(['outcome'=>'STOCK_CANCELLED','order_id'=>$order->get_id()]);
"""
