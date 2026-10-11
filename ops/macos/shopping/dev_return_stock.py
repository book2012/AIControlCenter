"""Isolated DEV whole-order return restock after Core receipt/inspection guards."""
import base64,hashlib,json,re,subprocess
from ops.macos.shopping.dev_order_operator import DevStockCancellation

class DevReturnStock:
    @staticmethod
    def expected(row,draft,case):
        if case['kind']!='RETURN' or not re.fullmatch(r'[a-f0-9]{8}',case['id']) or case['order_id']!=row['provider_order_id']:
            raise ValueError('RETURN_CASE_BINDING')
        value=DevStockCancellation.expected(row,draft)
        value.update(case_id=case['id'],return_receipt=hashlib.sha256((value['tag']+':return:'+case['id']).encode()).hexdigest())
        return value
    def _run(self,expected,script):
        from ops.macos.shopping.dev_order_runtime import assert_isolation
        assert_isolation()
        encoded=base64.b64encode(json.dumps(expected).encode()).decode()
        r=subprocess.run(['docker','--context','colima-aicontrolcenter-commerce','exec','-i','aicc-order-dev-wordpress-1','php'],input=script.replace('__PAYLOAD__',encoded),capture_output=True,text=True,timeout=25)
        if r.returncode:raise ValueError('RETURN_RECONCILIATION_REQUIRED')
        value=json.loads(r.stdout)
        if value.get('outcome')!='STOCK_RETURNED' or value.get('order_id')!=expected['order_id'] or value.get('case_id')!=expected['case_id']:
            raise ValueError('RETURN_RECONCILIATION_REQUIRED')
        return value
    def __call__(self,row,draft,case):return self.apply(self.expected(row,draft,case))
    def apply(self,expected):return self._run(expected,RETURN_STOCK_PHP)
    def reconcile(self,row,draft,case):return self._run(self.expected(row,draft,case),RETURN_RECONCILE_PHP)

RETURN_STOCK_PHP="""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
add_filter('pre_wp_mail',fn()=>false);
$cfg=json_decode(base64_decode('__PAYLOAD__'),true);global $wpdb;
if($wpdb->get_var("SELECT GET_LOCK('aicc_dev_stock_confirmation',5)")!=='1'){exit(3);}
try {
 $bad=$wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND engine IS NOT NULL AND engine<>'InnoDB'",DB_NAME));
 if((int)$bad!==0){throw new Exception('ENGINE');}
 $wpdb->query('START TRANSACTION');$order=wc_get_order($cfg['order_id']);
 if(!$order || $order->get_meta('_aicc_order_operation')!==$cfg['tag'] || $order->get_meta('_aicc_delivery_digest')!==$cfg['digest']){throw new Exception('BINDING');}
 $items=array_values($order->get_items());$actual=[];
 foreach($items as $item){$actual[]=['product'=>$item->get_product_id(),'variation'=>$item->get_variation_id(),'quantity'=>$item->get_quantity()];}
 if($actual!=$cfg['items']){throw new Exception('ITEM_BINDING');}
 if(hash('sha256',$cfg['tag'].':return:'.$cfg['case_id'])!==$cfg['return_receipt']){throw new Exception('RETURN_RECEIPT_BINDING');}
 if(!preg_match('/^[a-f0-9]{8}$/',$cfg['case_id']) || $order->get_meta('_aicc_stock_cancellation')!==''){throw new Exception('RETURN_BINDING');}
 $receipt=$order->get_meta('_aicc_stock_return');
 if($receipt!=='' && $receipt!==$cfg['return_receipt']){throw new Exception('RECEIPT_BINDING');}
 if($receipt===''){
  if(!in_array($order->get_status(),['on-hold','processing','completed'],true)){throw new Exception('STATUS');}
  if($order->get_meta('_aicc_stock_confirmation')!==$cfg['tag']){throw new Exception('NOT_CONFIRMED');}
  if(!$order->get_data_store()->get_stock_reduced($order->get_id())){throw new Exception('NOT_REDUCED');}
  foreach($items as $item){if((int)$item->get_meta('_reduced_stock',true)!==$item->get_quantity()){throw new Exception('REDUCED_BINDING');}}
  wc_maybe_increase_stock_levels($order->get_id());
  foreach($items as $item){$item->read_meta_data(true);if($item->get_meta('_reduced_stock',true)!==''){throw new Exception('RESTORATION_UNVERIFIED');}}
  if($order->get_data_store()->get_stock_reduced($order->get_id())){throw new Exception('RESTORATION_FLAG');}
  // Physical return restoration does not execute or claim a payment refund.
  $order->update_meta_data('_aicc_stock_return',$cfg['return_receipt']);$order->save();
 }
 $wpdb->query('COMMIT');$stocks=[];
 foreach($items as $item){$p=$item->get_product();$stocks[]=['variation'=>$item->get_variation_id(),'quantity'=>$p->get_stock_quantity()];}
 echo json_encode(['outcome'=>'STOCK_RETURNED','order_id'=>$order->get_id(),'case_id'=>$cfg['case_id'],'stocks'=>$stocks]);
} catch(Throwable $e){$wpdb->query('ROLLBACK');exit(4);}
finally{$wpdb->get_var("SELECT RELEASE_LOCK('aicc_dev_stock_confirmation')");}
"""

RETURN_RECONCILE_PHP="""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
$cfg=json_decode(base64_decode('__PAYLOAD__'),true);$order=wc_get_order($cfg['order_id']);
if(!$order || $order->get_meta('_aicc_order_operation')!==$cfg['tag'] || $order->get_meta('_aicc_delivery_digest')!==$cfg['digest'] || $order->get_meta('_aicc_stock_return')!==$cfg['return_receipt'] || $order->get_meta('_aicc_stock_cancellation')!==''){exit(3);}
if(!preg_match('/^[a-f0-9]{8}$/',$cfg['case_id']) || hash('sha256',$cfg['tag'].':return:'.$cfg['case_id'])!==$cfg['return_receipt']){exit(6);}
$actual=[];foreach($order->get_items() as $item){
 $actual[]=['product'=>$item->get_product_id(),'variation'=>$item->get_variation_id(),'quantity'=>$item->get_quantity()];
 if($item->get_meta('_reduced_stock',true)!==''){exit(4);}
}
if($actual!=$cfg['items'] || $order->get_data_store()->get_stock_reduced($order->get_id())){exit(5);}
echo json_encode(['outcome'=>'STOCK_RETURNED','order_id'=>$order->get_id(),'case_id'=>$cfg['case_id']]);
"""
