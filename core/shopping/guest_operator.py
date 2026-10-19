"""Customer-aware order/operator presentation over private Core state; no live writes."""
import hashlib,json,re,sqlite3
from core.shopping.order_core.guest_checkout import fingerprint
from core.shopping.order_core.telegram import OrderTelegramIntegration
from core.shopping.public_order_number import public_order_number, is_public_order_number

def order_date(value):
    from datetime import datetime,timezone
    from zoneinfo import ZoneInfo
    if not value:return "일자 미확인"
    try:
        date=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if date.tzinfo is None:date=date.replace(tzinfo=timezone.utc)
        return date.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
    except (ValueError,TypeError):return "일자 미확인"

def order_identity(row):
    name=row.get("customer_name") or row.get("delivery",{}).get("first_name") or "이름 미등록"
    items=row.get("items") or row.get("quote",{}).get("line_items",[])
    products=", ".join(str(v.get("name","상품 미확인"))+" / "+str(v.get("option") or "기본")+" / "+str(v.get("quantity",0))+"개" for v in items)
    return str(name)+" · "+str(row.get("phone") or "번호 미등록")+"\n주문일: "+order_date(row.get("requested_at"))+"\n"+products

PHONE_PATTERN=r"(?:010[0-9]{8}|010-[0-9]{4}-[0-9]{4})"

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
            phone=local_phone(body["billing"]["phone"])
            result.append({**row,"phone":phone,"order_number":public_order_number(requested_at=row.get("requested_at"),phone=phone,entropy=row.get("reference") or row["operation_key"]),"quote":body["quote"],"delivery":body["shipping"]})
        return result
    def _order_number(self,row):
        return row.get("order_number") or public_order_number(requested_at=row.get("requested_at"),phone=row.get("phone",""),entropy=row.get("reference") or row.get("operation_key") or row.get("provider_order_id"))
    def message(self,payload):
        matches=[r for r in self.rows() if r["reference"]==payload["reference"] and r["provider_order_id"]==payload["provider_order_id"]]
        if len(matches)!=1:return OrderTelegramIntegration._message(payload)
        r=matches[0];phone=r["phone"];state=payload["review_state"]
        if self.aftersales and self.aftersales.cancellation(r["provider_order_id"])["state"]!="NONE":
            return "주문 "+self._order_number(r)+" · "+("취소완료 · 재고 복원 확인" if self.display_state(r)=="CANCELLED" else "취소 결과 확인중")
        title={"PENDING_REVIEW":" 고객님 주문","CONFIRMED":" 고객님 주문확인 완료 · 재고 차감 완료",
               "REJECTED":" 고객님 주문 거절","STOCK_BLOCKED":" 고객님 주문확정 보류 · 재고 확인 필요"}.get(state," 고객님 주문 상태")
        items="\n".join(v["name"]+" / "+v["option"]+" / "+str(v["quantity"])+"개" for v in r["quote"]["line_items"])
        text=phone+title+"\n주문 "+self._order_number(r)+" · "+str(r["delivery"].get("first_name") or "이름 미등록")+"\n주문일: "+order_date(r.get("requested_at"))+"\n"+items+"\n"+payload["total"]+" "+payload["currency"]
        if state in ("PENDING_REVIEW","STOCK_BLOCKED"):
            text+="\n답장: "+phone+" 고객 주문확인\n여러 주문은: "+phone+" 고객 주문확인 #"+self._order_number(r)
        text+="\n상세: 주문상세 #"+self._order_number(r)+" · 전체: 주문목록"
        return text
    def display_state(self,row):
        if row["state"]!="CONFIRMED" or self.aftersales is None:return row["state"]
        if self.aftersales.refund(row["provider_order_id"])["state"]=="RECORDED":return "REFUND_RECORDED"
        cancellation=self.aftersales.cancellation(row["provider_order_id"])["state"]
        if cancellation!="NONE":return "CANCELLED" if cancellation=="CANCELLED" else "CANCELLATION_PENDING"
        returned=self.aftersales.return_status(row["provider_order_id"])["state"]
        if returned!="NONE":return returned
        fulfillment=self.aftersales.admin_fulfillment(row["provider_order_id"])
        return "COMPLETED" if fulfillment["state"]=="DELIVERED" else "SHIPPED" if fulfillment["state"]=="SHIPPED" else "READY_TO_SHIP" if self.aftersales.payment(row["provider_order_id"])["state"]=="PAID" else "AWAITING_DEPOSIT"
    def admin_orders(self,limit=50):
        rows=self.rows()[:max(1,min(int(limit),100))]
        return [{"order_id":r["provider_order_id"],"order_number":self._order_number(r),"phone":r["phone"],"customer_name":r["delivery"].get("first_name",""),"state":r["state"],"display_state":self.display_state(r),"requested_at":r.get("requested_at"),
            "total":r["quote"]["final_total"],"currency":r["quote"]["currency"],"items":[{"name":v["name"],"option":v.get("option"),"quantity":v["quantity"]} for v in r["quote"]["line_items"]]} for r in rows]
    def admin_detail(self,order_id):
        rows=[r for r in self.rows() if r["provider_order_id"]==int(order_id)]
        if len(rows)!=1:return None
        r=rows[0];d=r["delivery"]
        return {"order_id":r["provider_order_id"],"order_number":self._order_number(r),"phone":r["phone"],"customer_name":r["delivery"].get("first_name",""),"state":r["state"],"display_state":self.display_state(r),"requested_at":r.get("requested_at"),
            "total":r["quote"]["final_total"],"currency":r["quote"]["currency"],"items":[{"name":v["name"],"option":v.get("option"),"quantity":v["quantity"]} for v in r["quote"]["line_items"]],
            "delivery":{"recipient":d.get("first_name",""),"postcode":d.get("postcode",""),"address1":d.get("address_1",""),"address2":d.get("address_2","")}}
    def list_message(self,limit=None,phone=None,state=None,page=0,scope="ALL"):
        rows=[r for r in self.rows() if phone is None or r["phone"]==phone]
        if state is not None:rows=[r for r in rows if self.display_state(r)==state]
        if limit is not None:rows=rows[:max(1,min(int(limit),100))]
        page=max(0,min(int(page),100000));page_size=5;total=len(rows);pages=max(1,(total+page_size-1)//page_size)
        if page>=pages:page=pages-1
        if not rows:return "현재 확인 가능한 주문이 없습니다."
        labels={"REFUND_RECORDED":"환불완료 기록","RETURN_APPROVED":"반품승인","RETURN_RECEIVED":"반품회수·검수대기","RETURN_RESTOCK_PENDING":"반품재고 확인중","RETURN_RESTOCK_UNKNOWN":"반품재고 확인중","RETURN_RESTOCKED":"반품검수완료·환불검토","CANCELLED":"취소완료","CANCELLATION_PENDING":"취소 확인중","PENDING_REVIEW":"확인대기","CONFIRMED":"확인완료","READY_TO_SHIP":"배송준비","AWAITING_DEPOSIT":"입금대기","SHIPPED":"배송중","COMPLETED":"배송완료","REJECTED":"거절","STOCK_BLOCKED":"재고확인"}
        lines=["AICC_ORDER_PAGE:"+scope+":"+(state or "ALL")+":"+str(page)+":"+str(pages)+":"+str(total),
               ("고객 "+phone+" 주문 " if phone else (labels.get(state,state)+" 주문 " if state else "전체 주문 "))+str(total)+"건 · "+str(page+1)+"/"+str(pages)]
        for r in rows[page*page_size:(page+1)*page_size]:
            display=self.display_state(r)
            lines.append(self._order_number(r)+" · "+r["phone"]+" · "+labels.get(display,display)+" · "+str(r["quote"]["final_total"])+" "+str(r["quote"]["currency"]))
            lines.append("고객: "+str(r["delivery"].get("first_name") or "이름 미등록")+" · 주문일: "+order_date(r.get("requested_at")))
            lines.extend("- "+v["name"]+" / "+str(v.get("option") or "기본")+" / "+str(v["quantity"])+"개" for v in r["quote"]["line_items"])
            if self.aftersales:
                refund=self.aftersales.refund(r["provider_order_id"])
                if refund["state"]=="RECORDED":lines.append("환불완료 기록: "+refund["amount"]+" "+refund["currency"])
                shipment=self.aftersales.admin_fulfillment(r["provider_order_id"])
                if self.aftersales.cancellation(r["provider_order_id"])["state"]!="NONE":
                    lines.append("취소 상태를 확인해 주세요.")
                    continue
                lines.append("입금: "+("확인완료" if self.aftersales.payment(r["provider_order_id"])["state"]=="PAID" else "대기"))
                if shipment["tracking"]:lines.append(shipment["carrier"]+" · "+shipment["tracking"])
            lines.append("")
        return "\n".join(lines)
    def _identifier_rows(self, identifier, phone=None):
        token=str(identifier).strip().removeprefix("#")
        rows=self.rows()
        if is_public_order_number(token):
            rows=[r for r in rows if self._order_number(r)==token]
        else:
            try:provider_id=int(token)
            except ValueError:return []
            rows=[r for r in rows if r["provider_order_id"]==provider_id]
        return [r for r in rows if phone is None or r["phone"]==phone]
    def detail_message(self,order_id,phone=None):
        rows=self._identifier_rows(order_id,phone)
        if len(rows)!=1:return "해당 주문을 찾지 못했습니다." if not rows else "주문을 구분할 수 없습니다."
        r=rows[0];d=r["delivery"];labels={"REFUND_RECORDED":"환불완료 기록","RETURN_APPROVED":"반품승인","RETURN_RECEIVED":"반품회수·검수대기","RETURN_RESTOCK_PENDING":"반품재고 확인중","RETURN_RESTOCK_UNKNOWN":"반품재고 확인중","RETURN_RESTOCKED":"반품검수완료·환불검토","CANCELLED":"취소완료","CANCELLATION_PENDING":"취소 확인중","PENDING_REVIEW":"확인대기","CONFIRMED":"확인완료","READY_TO_SHIP":"배송준비","AWAITING_DEPOSIT":"입금대기","SHIPPED":"배송중","COMPLETED":"배송완료","REJECTED":"거절","STOCK_BLOCKED":"재고확인"}
        items="\n".join("- "+v["name"]+" / "+str(v.get("option") or "기본")+" / "+str(v["quantity"])+"개" for v in r["quote"]["line_items"])
        address=" ".join(v for v in (d.get("address_1",""),d.get("address_2","")) if v).strip()
        display=self.display_state(r)
        return ("주문 "+self._order_number(r)+" 상세\n상태: "+labels.get(display,display)+"\n고객: "+r["phone"]+"\n주문일: "+order_date(r.get("requested_at"))+"\n수령인: "+str(d.get("first_name",""))+"\n우편번호: "+str(d.get("postcode",""))+"\n주소: "+address+"\n\n"+items+"\n총액: "+str(r["quote"]["final_total"])+" "+str(r["quote"]["currency"]))
    def resolve(self,text,update_id=None,actor=None):
        if self.inquiry_queue is not None and update_id is not None:
            reply=self.inquiry_queue.command(text,update_id)
            if reply is not None:
                self.inquiry_queue.export(self.inquiry_queue.path.with_name("inquiry-learning.jsonl"))
                return None,None,reply
        if self.aftersales is not None and update_id is not None:
            reply=self.aftersales.operator_command(text,update_id,actor=actor)
            if reply is not None:return None,None,reply
        clean=text.strip()
        if clean in ("주문목록","주문 목록","주문목록 메뉴","주문 목록 메뉴"):
            return None,None,"주문 목록 보기를 선택해 주세요."
        if re.fullmatch(PHONE_PATTERN,clean):return None,None,self.list_message(phone=local_phone(clean))
        mphone_list=re.fullmatch(r"("+PHONE_PATTERN+r")\s*(?:고객(?:님)?\s*)?(?:주문\s*)?(?:상태|목록|내역)",clean)
        if mphone_list:return None,None,self.list_message(phone=local_phone(mphone_list[1]))
        if clean in ("주문내역","주문 내역","전체 주문","전체 주문내역","전체 주문 목록"):return None,None,self.list_message()
        mnumeric_order=re.fullmatch(r"#?([0-9]{10,18})",clean)
        if mnumeric_order:return None,None,self.detail_message(mnumeric_order[1])
        mphone_action=re.fullmatch(r"("+PHONE_PATTERN+r")\s*(?:고객(?:님)?\s*)?(입금\s*확인|배송\s*완료|배송|주문\s*취소|취소\s*확인)(?:\s*#([0-9]{1,18}))?(?:\s+([가-힣A-Za-z0-9 ._-]{2,40})\s+([A-Za-z0-9-]{5,40}))?",clean)
        if mphone_action and self.aftersales is not None and update_id is not None:
            phone=local_phone(mphone_action[1]);rows=[r for r in self.rows() if r["phone"]==phone]
            if mphone_action[3]:rows=self._identifier_rows(mphone_action[3],phone)
            if len(rows)!=1:
                return None,None,("주문번호를 함께 입력해 주세요: "+", ".join("#"+str(r["provider_order_id"]) for r in rows) if rows else "해당 고객 주문을 찾지 못했습니다.")
            action=re.sub(r"\s","",mphone_action[2]);number=str(rows[0]["provider_order_id"])
            if action=="배송" and not mphone_action[4]:return None,None,"배송 #"+number+" 택배사 운송장번호 형식으로 입력해 주세요."
            command=action+" #"+str(rows[0]["provider_order_id"])+((" "+mphone_action[4]+" "+mphone_action[5]) if action=="배송" else "")
            return None,None,self.aftersales.operator_command(command,update_id)
        if clean in ("주문목록 상태 메뉴","주문 상태 메뉴"):return None,None,"조회할 주문 상태를 선택해 주세요."
        mlist_page=re.fullmatch(r"주문목록 (전체|상태) ([A-Z_]+) ([0-9]{1,6})",clean)
        if mlist_page:
            mode,value,page=mlist_page.groups()
            allowed={"PENDING_REVIEW","AWAITING_DEPOSIT","READY_TO_SHIP","SHIPPED","COMPLETED","RETURN_APPROVED","RETURN_RECEIVED","RETURN_RESTOCKED","REFUND_RECORDED","CANCELLED","REJECTED","STOCK_BLOCKED"}
            if mode=="전체" and value=="ALL":return None,None,self.list_message(state=None,page=int(page),scope="ALL")
            if mode=="상태" and value in allowed:return None,None,self.list_message(state=value,page=int(page),scope="STATUS")
            return None,None,"선택한 주문 상태를 조회할 수 없습니다."
        mlist=re.fullmatch(r"주문\s*목록(?:\s+([1-9][0-9]?))?",clean)
        if mlist:return None,None,self.list_message(int(mlist[1]) if mlist[1] else None)
        mdetail=re.fullmatch(r"(?:주문\s*상세|주문번호\s*확인)\s*#?([1-9][0-9]*)",clean)
        if mdetail:return None,None,self.detail_message(int(mdetail[1]))
        mphone_detail=re.fullmatch(r"("+PHONE_PATTERN+r")\s*고객(?:님)?\s*주문\s*상세\s*#?([1-9][0-9]*)",clean)
        if mphone_detail:return None,None,self.detail_message(int(mphone_detail[2]),local_phone(mphone_detail[1]))
        match=re.fullmatch(r"("+PHONE_PATTERN+r")\s*고객(?:님)?\s*주문\s*(확인|확정|거절|상태)(?:\s*#([0-9]{1,18}))?\s*",text)
        if not match:return None,None,None
        phone=local_phone(match[1]);decision={"확인":"CONFIRMED","확정":"CONFIRMED","거절":"REJECTED","상태":"STATUS"}[match[2]]
        rows=[r for r in self.rows() if r["phone"]==phone]
        if match[3]:rows=self._identifier_rows(match[3],phone)
        elif decision!="STATUS":
            pending=[r for r in rows if r["state"]=="PENDING_REVIEW"]
            if pending:rows=pending
        if len(rows)!=1:
            choices=", ".join("#"+str(r["provider_order_id"]) for r in rows)
            return None,None,("주문을 구분해 주세요: "+choices+"\n전화번호 고객 주문확인 #주문번호" if rows else "해당 고객 주문을 찾지 못했습니다.")
        if decision=="STATUS":return None,None,self.detail_message(rows[0]["provider_order_id"],phone)
        return rows[0]["reference"],decision,None

