"""Private DEV operator UX and atomic Woo stock confirmation. No PROD composition."""
import base64, hashlib, json, re, sqlite3, subprocess
from pathlib import Path
from core.shopping.order_core.guest_checkout import fingerprint
from core.shopping.order_core.telegram import OrderTelegramIntegration

def local_phone(value):
    value=re.sub(r"[^0-9+]","",value)
    if value.startswith("+82"):value="0"+value[3:]
    if not re.fullmatch(r"010[0-9]{8}",value):raise ValueError("PHONE_INVALID")
    return value

class DevOperatorAdapter:
    def __init__(self,*,ledger,store,inquiry_queue=None,aftersales=None):self.ledger=ledger;self.store=store;self.inquiry_queue=inquiry_queue;self.aftersales=aftersales
    def rows(self):
        with sqlite3.connect("file:"+str(self.store.path.resolve())+"?mode=ro",uri=True) as c:
            drafts={r[0]: (r[1],r[2]) for r in c.execute("SELECT operation_key,body,digest FROM checkout_delivery WHERE state='CONFIRMED'")}
        result=[]
        for row in self.ledger.operator_orders():
            raw=drafts.get(row["operation_key"])
            if raw is None:continue
            body=json.loads(raw[0])
            if fingerprint(body)!=raw[1]:raise ValueError("PRIVATE_DRAFT_CORRUPT")
            result.append({**row,"phone":local_phone(body["billing"]["phone"]),"quote":body["quote"],"delivery":body["shipping"]})
        return result
    def message(self,payload):
        matches=[r for r in self.rows() if r["reference"]==payload["reference"] and r["provider_order_id"]==payload["provider_order_id"]]
        if len(matches)!=1:return OrderTelegramIntegration._message(payload)
        r=matches[0];phone=r["phone"];state=payload["review_state"]
        title={"PENDING_REVIEW":" 고객님 주문","CONFIRMED":" 고객님 주문확인 완료 · 재고 차감 완료",
               "REJECTED":" 고객님 주문 거절","STOCK_BLOCKED":" 고객님 주문확정 보류 · 재고 확인 필요"}.get(state," 고객님 주문 상태")
        items="\n".join(v["name"]+" / "+v["option"]+" / "+str(v["quantity"])+"개" for v in r["quote"]["line_items"])
        text=phone+title+"\n주문 #"+str(r["provider_order_id"])+"\n"+items+"\n"+payload["total"]+" "+payload["currency"]
        if state in ("PENDING_REVIEW","STOCK_BLOCKED"):
            text+="\n답장: "+phone+" 고객 주문확인\n여러 주문은: "+phone+" 고객 주문확인 #"+str(r["provider_order_id"])
        text+="\n상세: 주문상세 #"+str(r["provider_order_id"])+" · 전체: 주문목록"
        return text
    def display_state(self,row):
        if row["state"]!="CONFIRMED" or self.aftersales is None:return row["state"]
        fulfillment=self.aftersales.admin_fulfillment(row["provider_order_id"])
        return "COMPLETED" if fulfillment["state"]=="DELIVERED" else "SHIPPED" if fulfillment["state"]=="SHIPPED" else "READY_TO_SHIP"
    def admin_orders(self,limit=50):
        rows=self.rows()[:max(1,min(int(limit),100))]
        return [{"order_id":r["provider_order_id"],"phone":r["phone"],"state":r["state"],"display_state":self.display_state(r),"requested_at":r.get("requested_at"),
            "total":r["quote"]["final_total"],"currency":r["quote"]["currency"],"items":[{"name":v["name"],"option":v.get("option"),"quantity":v["quantity"]} for v in r["quote"]["line_items"]]} for r in rows]
    def admin_detail(self,order_id):
        rows=[r for r in self.rows() if r["provider_order_id"]==int(order_id)]
        if len(rows)!=1:return None
        r=rows[0];d=r["delivery"]
        return {"order_id":r["provider_order_id"],"phone":r["phone"],"state":r["state"],"display_state":self.display_state(r),"requested_at":r.get("requested_at"),
            "total":r["quote"]["final_total"],"currency":r["quote"]["currency"],"items":[{"name":v["name"],"option":v.get("option"),"quantity":v["quantity"]} for v in r["quote"]["line_items"]],
            "delivery":{"recipient":d.get("first_name",""),"postcode":d.get("postcode",""),"address1":d.get("address_1",""),"address2":d.get("address_2","")}}
    def list_message(self,limit=10):
        rows=self.rows()[:max(1,min(int(limit),20))]
        if not rows:return "현재 확인 가능한 주문이 없습니다."
        labels={"PENDING_REVIEW":"확인대기","CONFIRMED":"확인완료","READY_TO_SHIP":"발송대기","SHIPPED":"배송중","COMPLETED":"처리완료","REJECTED":"거절","STOCK_BLOCKED":"재고확인"}
        lines=["최근 주문 "+str(len(rows))+"건"]
        for r in rows:
            item=r["quote"]["line_items"][0] if r["quote"]["line_items"] else {"name":"상품","option":"","quantity":0}
            more=" +"+str(len(r["quote"]["line_items"])-1) if len(r["quote"]["line_items"])>1 else ""
            display=self.display_state(r)
            lines.append("#"+str(r["provider_order_id"])+" · "+r["phone"]+" · "+labels.get(display,display)+" · "+str(r["quote"]["final_total"])+" "+str(r["quote"]["currency"])+"\n"+item["name"]+" / "+str(item.get("option") or "기본")+" / "+str(item["quantity"])+"개"+more)
        lines.append("상세보기: 주문상세 #주문번호")
        return "\n\n".join(lines)
    def detail_message(self,order_id,phone=None):
        rows=[r for r in self.rows() if r["provider_order_id"]==int(order_id) and (phone is None or r["phone"]==phone)]
        if len(rows)!=1:return "해당 주문을 찾지 못했습니다." if not rows else "주문을 구분할 수 없습니다."
        r=rows[0];d=r["delivery"];labels={"PENDING_REVIEW":"확인대기","CONFIRMED":"확인완료","READY_TO_SHIP":"발송대기","SHIPPED":"배송중","COMPLETED":"처리완료","REJECTED":"거절","STOCK_BLOCKED":"재고확인"}
        items="\n".join("- "+v["name"]+" / "+str(v.get("option") or "기본")+" / "+str(v["quantity"])+"개" for v in r["quote"]["line_items"])
        address=" ".join(v for v in (d.get("address_1",""),d.get("address_2","")) if v).strip()
        display=self.display_state(r)
        return ("주문 #"+str(r["provider_order_id"])+" 상세\n상태: "+labels.get(display,display)+"\n고객: "+r["phone"]+"\n수령인: "+str(d.get("first_name",""))+"\n우편번호: "+str(d.get("postcode",""))+"\n주소: "+address+"\n\n"+items+"\n총액: "+str(r["quote"]["final_total"])+" "+str(r["quote"]["currency"]))
    def resolve(self,text,update_id=None):
        if self.inquiry_queue is not None and update_id is not None:
            reply=self.inquiry_queue.command(text,update_id)
            if reply is not None:
                self.inquiry_queue.export(self.inquiry_queue.path.with_name("inquiry-learning.jsonl"))
                return None,None,reply
        if self.aftersales is not None and update_id is not None:
            reply=self.aftersales.operator_command(text,update_id)
            if reply is not None:return None,None,reply
        clean=text.strip()
        mlist=re.fullmatch(r"주문\s*목록(?:\s+([1-9][0-9]?))?",clean)
        if mlist:return None,None,self.list_message(int(mlist[1]) if mlist[1] else 10)
        mdetail=re.fullmatch(r"주문\s*상세\s*#?([1-9][0-9]*)",clean)
        if mdetail:return None,None,self.detail_message(int(mdetail[1]))
        mphone_detail=re.fullmatch(r"(010[0-9]{8}|010-[0-9]{4}-[0-9]{4})\s*고객(?:님)?\s*주문\s*상세\s*#?([1-9][0-9]*)",clean)
        if mphone_detail:return None,None,self.detail_message(int(mphone_detail[2]),local_phone(mphone_detail[1]))
        match=re.fullmatch(r"(010[0-9]{8}|010-[0-9]{4}-[0-9]{4})\s*고객(?:님)?\s*주문\s*(확인|확정|거절|상태)(?:\s*#([1-9][0-9]*))?\s*",text)
        if not match:return None,None,None
        phone=local_phone(match[1]);decision={"확인":"CONFIRMED","확정":"CONFIRMED","거절":"REJECTED","상태":"STATUS"}[match[2]]
        rows=[r for r in self.rows() if r["phone"]==phone]
        if match[3]:rows=[r for r in rows if r["provider_order_id"]==int(match[3])]
        elif decision!="STATUS":
            pending=[r for r in rows if r["state"]=="PENDING_REVIEW"]
            if pending:rows=pending
        if len(rows)!=1:
            choices=", ".join("#"+str(r["provider_order_id"]) for r in rows)
            return None,None,("주문을 구분해 주세요: "+choices+"\n전화번호 고객 주문확인 #주문번호" if rows else "해당 고객 주문을 찾지 못했습니다.")
        return rows[0]["reference"],decision,None

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
