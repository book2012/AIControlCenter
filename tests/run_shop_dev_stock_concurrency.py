"""Explicit synthetic Woo integration probe; isolated DEV only, no network messages."""
import argparse,base64,json,secrets,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ops.macos.shopping.dev_order_runtime import assert_isolation
from ops.macos.shopping.dev_order_operator import DevStockConfirmation,DevStockCancellation,CANCEL_RECONCILE_PHP
PREFIX='aicc-dev-stock-probe-'

def php(code):
    r=subprocess.run(['docker','--context','colima-aicontrolcenter-commerce','exec','-i','aicc-order-dev-wordpress-1','php'],input=code,capture_output=True,text=True,timeout=30)
    if r.returncode:raise RuntimeError('DEV_PROBE_PHP_FAILED')
    return json.loads(r.stdout)

HEADER="""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';add_filter('pre_wp_mail',fn()=>false);
"""

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute-dev',action='store_true');args=parser.parse_args()
    if not args.execute_dev:parser.error('explicit --execute-dev required')
    assert_isolation();token=PREFIX+secrets.token_hex(8)
    journal=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data')/(token+'.json')
    setup=HEADER+"$token="+json.dumps(token)+";"+r'''
$p=new WC_Product_Simple();$p->set_name($token);$p->set_sku($token);$p->set_status('private');$p->set_regular_price('1000');$p->set_manage_stock(true);$p->set_stock_quantity(1);$p->set_backorders('no');$p->save();
$orders=[];for($i=0;$i<2;$i++){
 $o=wc_create_order(['status'=>'pending']);$o->add_product($p,1);
 $o->update_meta_data('_aicc_probe',$token);$o->update_meta_data('_aicc_order_operation',$token.'-'.$i);$o->update_meta_data('_aicc_delivery_digest',$token);$o->calculate_totals();$o->save();$orders[]=$o->get_id();
}echo json_encode(['product'=>$p->get_id(),'orders'=>$orders]);
'''
    ids=php(setup);journal.write_text(json.dumps({'token':token,**ids}));journal.chmod(0o600)
    payloads=[{'order_id':oid,'tag':token+'-'+str(i),'digest':token,'items':[{'product':ids['product'],'variation':0,'quantity':1}]} for i,oid in enumerate(ids['orders'])]
    confirm=DevStockConfirmation(store=None);cancel=DevStockCancellation(store=None)
    def attempt(payload):
        try:return confirm.apply(payload)
        except RuntimeError:return None
    def quantity():
        return php(HEADER+'$p=wc_get_product('+str(ids['product'])+');echo json_encode($p->get_stock_quantity());')
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,payloads))
        assert sum(x is not None for x in results)==1, 'expected one winner'
        winner=payloads[next(i for i,x in enumerate(results) if x is not None)]
        assert quantity()==0,'stock oversold'
        assert confirm.apply(winner)['outcome']=='STOCK_CONFIRMED' and quantity()==0,'confirmation replay reduced twice'
        wrong={**winner,'digest':'wrong'}
        try:cancel.apply(wrong)
        except RuntimeError:pass
        else:raise AssertionError('unbound cancellation allowed')
        assert quantity()==0
        php(HEADER+'$o=wc_get_order('+str(winner['order_id'])+');$o->update_status("processing");echo json_encode(true);')
        try:cancel.apply(winner)
        except RuntimeError:pass
        else:raise AssertionError('processing order cancellation allowed')
        assert quantity()==0
        php(HEADER+'$o=wc_get_order('+str(winner['order_id'])+');$o->update_status("on-hold");echo json_encode(true);')
        with ThreadPoolExecutor(max_workers=2) as pool:receipts=list(pool.map(cancel.apply,[winner,winner]))
        assert all(x['outcome']=='STOCK_CANCELLED' for x in receipts)
        assert quantity()==1,'duplicate restoration'
        assert cancel.apply(winner)['outcome']=='STOCK_CANCELLED' and quantity()==1
        payload=base64.b64encode(json.dumps(winner).encode()).decode()
        assert php(CANCEL_RECONCILE_PHP.replace('__PAYLOAD__',payload))=={'outcome':'STOCK_CANCELLED','order_id':winner['order_id']}
        assert quantity()==1
        assert attempt(winner) is None and quantity()==1,'cancelled order re-confirmed'
        print(json.dumps({'passed':True,'checks':['one stock / two concurrent orders','confirmation replay','binding denial','processing cancellation denied','concurrent cancellation restores once','cancellation replay','cancelled confirmation denied','read-only cancellation reconciliation'],'environment':'DEV','external_messages':0,'prod_mutation':False}),flush=True)
    finally:
        encoded=base64.b64encode(json.dumps(ids).encode()).decode()
        cleanup=HEADER+'$token='+json.dumps(token)+';$ids=json_decode(base64_decode('+json.dumps(encoded)+'),true);'+r'''
foreach($ids['orders'] as $id){$o=wc_get_order($id);if(!$o || $o->get_meta('_aicc_probe')!==$token){exit(3);}$o->delete(true);}
$p=wc_get_product($ids['product']);if(!$p || $p->get_sku()!==$token){exit(4);}$p->delete(true);echo json_encode(['cleaned'=>true]);
'''
        assert php(cleanup)['cleaned'];journal.unlink();print('SYNTHETIC_FIXTURES_CLEANED',flush=True)

if __name__=='__main__':main()
