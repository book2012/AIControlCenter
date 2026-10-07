"""Customer-aware order/operator presentation over private Core state; no live writes."""
import hashlib,json,re,sqlite3
from core.shopping.order_core.guest_checkout import fingerprint
from core.shopping.order_core.telegram import OrderTelegramIntegration

def local_phone(value):
    value=re.sub(r"[^0-9+]","",value)
    if value.startswith("+82"):value="0"+value[3:]
    if not re.fullmatch(r"010[0-9]{8}",value):raise ValueError("PHONE_INVALID")
    return value

class GuestOperatorAdapter:
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
        return "COMPLETED" if fulfillment["state"]=="DELIVERED" else "SHIPPED" if fulfillment["state"]=="SHIPPED" else "READY_TO_SHIP" if self.aftersales.payment(row["provider_order_id"])["state"]=="PAID" else "AWAITING_DEPOSIT"
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
    def list_message(self,limit=None,phone=None):
        rows=[r for r in self.rows() if phone is None or r["phone"]==phone]
        if limit is not None:rows=rows[:max(1,min(int(limit),100))]
        if not rows:return "현재 확인 가능한 주문이 없습니다."
        labels={"PENDING_REVIEW":"확인대기","CONFIRMED":"확인완료","READY_TO_SHIP":"배송준비","AWAITING_DEPOSIT":"입금대기","SHIPPED":"배송중","COMPLETED":"배송완료","REJECTED":"거절","STOCK_BLOCKED":"재고확인"}
        lines=[("고객 "+phone+" 주문 " if phone else "전체 주문 ")+str(len(rows))+"건"]
        for r in rows:
            display=self.display_state(r)
            lines.append("#"+str(r["provider_order_id"])+" · "+r["phone"]+" · "+labels.get(display,display)+" · "+str(r["quote"]["final_total"])+" "+str(r["quote"]["currency"]))
            lines.extend("- "+v["name"]+" / "+str(v.get("option") or "기본")+" / "+str(v["quantity"])+"개" for v in r["quote"]["line_items"])
            if self.aftersales:
                shipment=self.aftersales.admin_fulfillment(r["provider_order_id"])
                lines.append("입금: "+("확인완료" if self.aftersales.payment(r["provider_order_id"])["state"]=="PAID" else "대기"))
                if shipment["tracking"]:lines.append(shipment["carrier"]+" · "+shipment["tracking"])
            lines.append("")
        lines.append("상세보기: 주문상세 #주문번호")
        return "\n".join(lines)
    def detail_message(self,order_id,phone=None):
        rows=[r for r in self.rows() if r["provider_order_id"]==int(order_id) and (phone is None or r["phone"]==phone)]
        if len(rows)!=1:return "해당 주문을 찾지 못했습니다." if not rows else "주문을 구분할 수 없습니다."
        r=rows[0];d=r["delivery"];labels={"PENDING_REVIEW":"확인대기","CONFIRMED":"확인완료","READY_TO_SHIP":"배송준비","AWAITING_DEPOSIT":"입금대기","SHIPPED":"배송중","COMPLETED":"배송완료","REJECTED":"거절","STOCK_BLOCKED":"재고확인"}
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
        if re.fullmatch(r"010[0-9]{8}|010-[0-9]{4}-[0-9]{4}",clean):return None,None,self.list_message(phone=local_phone(clean))
        mphone_list=re.fullmatch(r"(010[0-9]{8}|010-[0-9]{4}-[0-9]{4})\s*(?:고객(?:님)?\s*)?(?:주문\s*)?(?:상태|목록|내역)",clean)
        if mphone_list:return None,None,self.list_message(phone=local_phone(mphone_list[1]))
        if clean in ("주문내역","주문 내역","전체 주문","전체 주문내역","전체 주문 목록"):return None,None,self.list_message()
        mphone_action=re.fullmatch(r"(010[0-9]{8}|010-[0-9]{4}-[0-9]{4})\s*(?:고객(?:님)?\s*)?(입금\s*확인|배송\s*완료|배송)(?:\s*#([1-9][0-9]*))?(?:\s+([가-힣A-Za-z0-9 ._-]{2,40})\s+([A-Za-z0-9-]{5,40}))?",clean)
        if mphone_action and self.aftersales is not None and update_id is not None:
            phone=local_phone(mphone_action[1]);rows=[r for r in self.rows() if r["phone"]==phone]
            if mphone_action[3]:rows=[r for r in rows if r["provider_order_id"]==int(mphone_action[3])]
            if len(rows)!=1:
                return None,None,("주문번호를 함께 입력해 주세요: "+", ".join("#"+str(r["provider_order_id"]) for r in rows) if rows else "해당 고객 주문을 찾지 못했습니다.")
            action=re.sub(r"\s","",mphone_action[2]);number=str(rows[0]["provider_order_id"])
            if action=="배송" and not mphone_action[4]:return None,None,"배송 #"+number+" 택배사 운송장번호 형식으로 입력해 주세요."
            command=action+" #"+number+((" "+mphone_action[4]+" "+mphone_action[5]) if action=="배송" else "")
            return None,None,self.aftersales.operator_command(command,update_id)
        mlist=re.fullmatch(r"주문\s*목록(?:\s+([1-9][0-9]?))?",clean)
        if mlist:return None,None,self.list_message(int(mlist[1]) if mlist[1] else None)
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
        if decision=="STATUS":return None,None,self.detail_message(rows[0]["provider_order_id"],phone)
        return rows[0]["reference"],decision,None

