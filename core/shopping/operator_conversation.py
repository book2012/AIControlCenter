from core.shopping.guest_operator import order_identity
"""Private, actor-scoped operator dialogue and confirmation; no model-generated execution."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
from core.shopping.operator_intent import validate_plan,resolve_explicit_slots

READ_ACTIONS={"ORDER_LIST","ORDER_DETAIL","PRODUCT_LIST","PRODUCT_STATUS","RETURN_RECONCILE"}
ORDER_ACTIONS={"ORDER_DETAIL","ORDER_CONFIRM","DEPOSIT_CONFIRM","SHIP","DELIVERED","CANCEL"}
PRODUCT_ACTIONS={"PRODUCT_STATUS","SET_STOCK","SET_PRICE","SET_SALE","UNSALE","HIDE","SHOW"}

class OperatorConversation:
    def __init__(self, *, path, judge, orders, products, validate_product, executor,
                 clock=time.time, approval_seconds=1800, remind_seconds=900):
        self.path=Path(path)
        if self.path.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        self.judge,self.orders,self.products,self.validate_product,self.executor=judge,orders,products,validate_product,executor
        self.clock,self.approval_seconds,self.remind_seconds=clock,approval_seconds,remind_seconds
        self.lock=threading.RLock()
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS dialogue_turns(update_id INTEGER PRIMARY KEY,actor TEXT NOT NULL,digest TEXT NOT NULL,state TEXT NOT NULL,reply TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS dialogue_sessions(actor TEXT PRIMARY KEY,plan TEXT,last_order INTEGER,request TEXT,proposal_id TEXT,state TEXT,created REAL,expires REAL)")
            c.execute("CREATE TABLE IF NOT EXISTS dialogue_notices(id TEXT PRIMARY KEY,actor TEXT,body TEXT NOT NULL,state TEXT NOT NULL,due REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS website_jobs(id TEXT PRIMARY KEY,actor TEXT NOT NULL,request TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL)")
        os.chmod(self.path,0o600)

    def _session(self, actor):
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row
            row=c.execute("SELECT * FROM dialogue_sessions WHERE actor=?",(actor,)).fetchone()
        return dict(row) if row else {}

    def _save(self, actor, plan, state, request, last_order=None):
        old=self._session(actor)
        now=self.clock();pid=secrets.token_hex(4)
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE dialogue_notices SET state='CANCELLED' WHERE actor=? AND state='PENDING' AND (id LIKE 'approval:%' OR id LIKE 'info:%')",(actor,))
            c.execute("INSERT INTO dialogue_sessions VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(actor) DO UPDATE SET plan=excluded.plan,last_order=excluded.last_order,request=excluded.request,proposal_id=excluded.proposal_id,state=excluded.state,created=excluded.created,expires=excluded.expires",
                (actor,json.dumps(plan,ensure_ascii=False),last_order or old.get("last_order"),request,pid,state,now,now+self.approval_seconds))
        return pid

    def _finish(self, update_id, reply):
        if type(reply) is not str or not 1<=len(reply)<=3500:
            reply="결과가 길거나 형식이 맞지 않습니다. 주문번호나 상품명을 지정해 다시 조회해 주세요."
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE dialogue_turns SET state='COMPLETED',reply=? WHERE update_id=? AND state='CLAIMED'",(reply,update_id))
        return reply

    def _command(self, plan):
        action=plan["action"]
        if action=="ORDER_LIST":return (plan["phone"]+" 주문목록" if plan.get("phone") else "주문목록"),None
        if action in ORDER_ACTIONS:
            rows=self.orders()
            if plan.get("phone"):rows=[r for r in rows if r["phone"]==plan["phone"]]
            if plan.get("order_id"):rows=[r for r in rows if r["order_id"]==plan["order_id"]]
            if not plan.get("order_id") and not plan.get("phone"):
                return None,"어느 주문인가요? 주문번호나 고객 휴대폰 번호를 알려주세요."
            if len(rows)!=1:
                return None,("주문을 골라주세요: "+"\n\n".join("#"+str(r["order_id"])+" · "+order_identity(r) for r in rows[:12]) if rows else "일치하는 주문을 찾지 못했습니다.")
            number=rows[0]["order_id"];plan["order_id"]=number
            if action=="ORDER_CONFIRM":return rows[0]["phone"]+" 고객 주문확인 #"+str(number),None
            if action=="SHIP":
                if not plan.get("carrier") or not plan.get("tracking"):return None,"택배사와 운송장번호를 알려주세요."
                if not re.fullmatch(r"[가-힣A-Za-z0-9 ._-]{2,40}",plan["carrier"]) or not re.fullmatch(r"[A-Za-z0-9-]{5,40}",plan["tracking"]):
                    return None,"택배사와 운송장번호 형식을 확인해 주세요."
                return "배송 #"+str(number)+" "+plan["carrier"]+" "+plan["tracking"],None
            prefix={"ORDER_DETAIL":"주문상세","DEPOSIT_CONFIRM":"입금확인","DELIVERED":"배송완료","CANCEL":"주문취소"}[action]
            return prefix+" #"+str(number),None
        if action=="REFUND_RECORD":
            if not plan.get("case_id"):return None,"송금 완료를 기록할 반품 케이스번호 8자리를 알려주세요."
            if not plan.get("price"):return None,"이미 송금한 환불 금액을 원 단위로 알려주세요."
            if not plan.get("evidence"):return None,"송금 완료 증빙의 참조번호를 알려주세요. 예: 증빙 BANK-20261012-001"
            return "환불기록 #"+plan["case_id"]+" "+str(plan["price"])+"원 증빙 "+plan["evidence"],None
        if action in {"RETURN_RECEIVE","RETURN_INSPECT","RETURN_RECONCILE"}:
            if not plan.get("case_id"):return None,"반품 케이스번호 8자리를 알려주세요. 예: a1b2c3d4"
            return "반품 "+{"RETURN_RECEIVE":"회수","RETURN_INSPECT":"검수완료","RETURN_RECONCILE":"복원확인"}[action]+" #"+plan["case_id"],None
        if action=="PRODUCT_LIST":
            category=plan.get("category") or "전체"
            if category not in {"전체","상의","하의","아우터","원피스","가방","액세서리","남성","all","top","bottom","outer","dress","bag","acc","men"}:
                return None,"상의·하의·아우터·원피스·가방·액세서리 중 카테고리를 알려주세요."
            return category+" 리스트",None
        if action in PRODUCT_ACTIONS:
            records=[r for r in self.products() if r["name"]==plan.get("product")]
            if len(records)!=1:return None,"상품명을 정확히 알려주세요. 상품 목록에서 이름을 확인할 수 있습니다."
            name=records[0]["name"]
            if action=="SET_STOCK":
                if "quantity" not in plan:return None,"재고를 몇 개로 변경할까요?"
                options=" ".join(plan[k] for k in ["color","size"] if plan.get(k))
                command=name+" "+options+" 재고 "+str(plan["quantity"])+"개로 변경"
            elif action in {"SET_PRICE","SET_SALE"}:
                if "price" not in plan:return None,"변경할 금액을 원 단위로 알려주세요."
                command=name+" "+("가격 " if action=="SET_PRICE" else "")+str(plan["price"])+"원으로 "+("변경" if action=="SET_PRICE" else "할인")
            else:command=name+" "+{"PRODUCT_STATUS":"재고 확인","UNSALE":"할인 취소","HIDE":"숨김","SHOW":"다시 공개"}[action]
            try:
                if self.validate_product(command) is None:return None,"상품 옵션과 변경 내용을 다시 확인해 주세요."
            except ValueError as error:return None,str(error)
            return command,None
        if action=="WEBSITE_TASK":return "홈페이지 개선 요청",None
        return None,"주문·입금·배송·반품·재고·가격 또는 홈페이지 개선 내용을 말씀해 주세요."

    def handle(self, text, update_id, actor):
        if type(update_id) is not int or not 0<=update_id<2**63-1 or not re.fullmatch(r"telegram-user-[0-9]+",actor):
            raise ValueError("OPERATOR_DIALOGUE_AUTH_REQUIRED")
        if type(text) is not str or not 1<=len(text)<=1500:return "내용을 1500자 이내로 알려주세요."
        digest=hashlib.sha256(text.encode()).hexdigest()
        with self.lock:
            with sqlite3.connect(self.path) as c:
                c.execute("BEGIN IMMEDIATE")
                row=c.execute("SELECT actor,digest,state,reply FROM dialogue_turns WHERE update_id=?",(update_id,)).fetchone()
                if row:
                    if row[0]!=actor or row[1]!=digest:raise ValueError("DIALOGUE_UPDATE_CONFLICT")
                    return row[3] if row[2]=="COMPLETED" else "이전 처리 결과 확인이 필요합니다. 같은 변경을 다시 실행하지 않습니다."
                c.execute("INSERT INTO dialogue_turns VALUES(?,?,?,'CLAIMED',NULL)",(update_id,actor,digest))
            session=self._session(actor);clean=text.strip()
            if clean in {"취소","아니","아니요","그만","그만해"}:
                if session.get("state") in {"EXECUTING","UNKNOWN"}:return self._finish(update_id,"불확실한 처리 결과를 먼저 확인해 주세요. 진행된 변경을 되돌리거나 다시 실행하지 않습니다.")
                self._save(actor,{},"CANCELLED","")
                return self._finish(update_id,"대기 중인 요청을 취소했습니다. 주문 자체를 취소한 것은 아닙니다.")
            if clean in {"대기사항","할일","할 일","알림","할일 목록"}:
                return self._finish(update_id,self.todo(actor))
            if clean in {"개선목록","홈페이지 개선목록"}:
                return self._finish(update_id,self.website_list(actor))
            if clean in {"응","네","예","확인","진행해","좋아","처리해","맞아"}:
                if session.get("state") not in {"WAITING_APPROVAL","WAITING_INFO"}:
                    return self._finish(update_id,"확인 대기 중인 요청이 없습니다. 처리할 내용을 알려주세요.")
                if self.clock()>session["expires"]:
                    self._save(actor,{},"EXPIRED","")
                    return self._finish(update_id,"확인 시간이 지났습니다. 최신 상태로 요청을 다시 알려주세요.")
                plan=json.loads(session["plan"]);command,question=self._command(plan)
                if question:return self._finish(update_id,question)
                if session["state"]!="WAITING_APPROVAL":return self._finish(update_id,"먼저 필요한 정보를 알려주세요.")
                # Claim before any commerce mutation. Restart/exception never retries.
                with sqlite3.connect(self.path) as c:
                    c.execute("UPDATE dialogue_sessions SET state='EXECUTING' WHERE actor=? AND state='WAITING_APPROVAL'",(actor,))
                    c.execute("UPDATE dialogue_notices SET state='CANCELLED' WHERE actor=? AND state='PENDING' AND (id LIKE 'approval:%' OR id LIKE 'info:%')",(actor,))
                try:
                    if plan["action"]=="WEBSITE_TASK":
                        job=session["proposal_id"]
                        with sqlite3.connect(self.path) as c:c.execute("INSERT INTO website_jobs VALUES(?,?,?,'WAITING_CODEX',?)",(job,actor,session["request"],self.clock()))
                        reply="홈페이지 개선 #"+job+"를 Codex 작업 대기에 기록했습니다. DEV 수정·테스트·검토 후 반영합니다. 운영 배포는 별도입니다."
                    else:reply=self.executor(command,update_id,actor)
                except Exception:
                    with sqlite3.connect(self.path) as c:
                        c.execute("UPDATE dialogue_sessions SET state='UNKNOWN',expires=? WHERE actor=?",(self.clock()+86400,actor))
                        c.execute("INSERT OR IGNORE INTO dialogue_notices VALUES(?,?,?,'PENDING',?)",("unknown:"+session["proposal_id"],actor,"처리 결과 확인 필요: "+command+"\n같은 변경을 재실행하지 말고 주문/재고 상태를 확인해 주세요.",self.clock()+300))
                    return self._finish(update_id,"처리 결과가 불확실합니다. 재실행하지 않고 주문 상태 확인이 필요합니다.")
                self._save(actor,plan,"COMPLETED",session["request"],plan.get("order_id"))
                return self._finish(update_id,reply)
            context={"orders":self.orders()[:20],"products":[{"name":r["name"],"sizes":r.get("size_options"),"colors":r.get("color_options")} for r in self.products()[:40]],
                "last_order_id":session.get("last_order") if self.clock()<=session.get("expires",0) else None}
            if session.get("state") in {"WAITING_INFO","WAITING_APPROVAL"} and self.clock()<=session["expires"]:
                context["previous_plan"]=json.loads(session["plan"])
            try:
                # Explicit read commands must not inherit a pending mutation intent.
                phone_list=re.fullmatch(r"(010[0-9]{8}|010-[0-9]{4}-[0-9]{4})(?:\s*(?:고객(?:님)?\s*)?(?:주문\s*)?(?:상태|목록|내역))?",clean)
                refund_record=re.fullmatch(r"환불(?:완료|기록)\s*#([a-f0-9]{8})\s+([1-9][0-9]{0,7})원\s+증빙\s+([가-힣A-Za-z0-9._-]{3,80})(?:\s*기록해)?",clean)
                if refund_record:plan=validate_plan({"action":"REFUND_RECORD","case_id":refund_record[1],"price":int(refund_record[2]),"evidence":refund_record[3]})
                elif clean in {"주문목록","주문 목록","주문내역","주문 내역","전체 주문","전체 주문내역","전체 주문 목록"}:plan={"action":"ORDER_LIST"}
                elif phone_list:plan={"action":"ORDER_LIST","phone":re.sub(r"[^0-9]","",phone_list[1])}
                elif re.fullmatch(r"주문\s*상세\s*#?([1-9][0-9]*)",clean):plan={"action":"ORDER_DETAIL","order_id":int(re.fullmatch(r"주문\s*상세\s*#?([1-9][0-9]*)",clean)[1])}
                else:
                    # Shipping follow-ups are deterministic when the pending request already
                    # identifies shipping; this avoids Qwen dropping carrier/typo-only slots.
                    shipping_followup=re.search(r"(?:운송장|운숭장|송장|택배사|택배)",clean)
                    previous_action=context.get("previous_plan",{}).get("action")
                    if shipping_followup and (previous_action=="SHIP" or "배송" in clean):
                        plan=resolve_explicit_slots({"action":"SHIP"},clean,context)
                    else:
                        plan=resolve_explicit_slots(validate_plan(self.judge(text,context)),text,context)
            except Exception:return self._finish(update_id,"AI가 요청을 정확히 해석하지 못했습니다. 주문번호·상품명과 처리 내용을 다시 알려주세요.")
            if plan["action"]=="TASK_LIST":return self._finish(update_id,self.todo(actor))
            if plan["action"]=="WEBSITE_LIST":return self._finish(update_id,self.website_list(actor))
            if session.get("state") in {"EXECUTING","UNKNOWN"} and plan["action"] not in READ_ACTIONS:
                return self._finish(update_id,"이전 처리 결과를 먼저 확인해 주세요. 불확실한 변경은 다시 실행하지 않습니다.")
            previous=context.get("previous_plan",{})
            same_target=not any(plan.get(k) is not None and previous.get(k) is not None and plan[k]!=previous[k] for k in ("order_id","phone","product","case_id"))
            if previous and same_target and plan["action"]==previous.get("action"):
                plan=validate_plan({**previous,**plan})
            command,question=self._command(plan)
            request=session.get("request",text) if "previous_plan" in context and plan["action"]==context["previous_plan"].get("action") else text
            if plan["action"]=="WEBSITE_TASK":
                request=text if "previous_plan" not in context else ("이전 요청: "+session.get("request","")+"\n최신 요청: "+text)[-1500:]
            if question:
                pid=self._save(actor,plan,"WAITING_INFO",request,plan.get("order_id"))
                with sqlite3.connect(self.path) as c:c.execute("INSERT INTO dialogue_notices VALUES(?,?,?,'PENDING',?)",("info:"+pid,actor,"추가 정보 대기: "+question,self.clock()+self.remind_seconds))
                return self._finish(update_id,question)
            if plan["action"] in READ_ACTIONS:
                reply=self.executor(command,update_id,actor)
                if session.get("state") not in {"EXECUTING","UNKNOWN"}:self._save(actor,plan,"READ",request,plan.get("order_id"))
                return self._finish(update_id,reply)
            pid=self._save(actor,plan,"WAITING_APPROVAL",request,plan.get("order_id"))
            detail=("이미 송금이 완료됐고 금액·증빙을 확인했다면 기록만 저장합니다. 실제 송금은 실행하지 않습니다. " if plan["action"]=="REFUND_RECORD" else "실물 회수·검수와 재판매 가능 여부를 확인하셨다면 " if plan["action"]=="RETURN_INSPECT" else "")
            reply=detail+"‘"+command+"’로 처리할까요? 맞으면 ‘응’, 변경하려면 내용을 알려주세요. 취소하려면 ‘아니’라고 해주세요."
            with sqlite3.connect(self.path) as c:
                c.execute("INSERT INTO dialogue_notices VALUES(?,?,?,'PENDING',?)",
                    ("approval:"+pid,actor,"확인 대기: "+command+"\n잊지 않도록 알려드립니다. ‘응’ 또는 ‘아니’로 답해주세요.",self.clock()+self.remind_seconds))
            return self._finish(update_id,reply)

    def todo(self, actor):
        session=self._session(actor);parts=[]
        if session.get("state") in {"WAITING_INFO","WAITING_APPROVAL"} and self.clock()<=session["expires"]:
            command,question=self._command(json.loads(session["plan"]))
            parts.append("대기 중: "+(question or command)+" · 승인 또는 추가 정보를 알려주세요.")
        if session.get("state") in {"EXECUTING","UNKNOWN"}:parts.append("처리 결과 확인이 필요합니다. 같은 변경은 다시 실행하지 않습니다.")
        labels={"PENDING_REVIEW":"주문확인","READY_TO_SHIP":"배송등록","AWAITING_DEPOSIT":"입금상태 확인"}
        parts.extend("주문 #"+str(r["order_id"])+" · "+labels[r["display_state"]]+"\n"+order_identity(r) for r in self.orders()[:30] if r.get("display_state") in labels)
        with sqlite3.connect(self.path) as c:
            count=c.execute("SELECT count(*) FROM website_jobs WHERE actor=? AND state NOT IN ('NO_CHANGE')",(actor,)).fetchone()[0]
        if count:parts.append("홈페이지 개선 "+str(count)+"건 · ‘개선목록’으로 진행 확인")
        return "\n".join(parts) or "현재 확인 대기 중인 작업이 없습니다."

    def website_list(self, actor):
        with sqlite3.connect(self.path) as c:
            rows=c.execute("SELECT id,request,state FROM website_jobs WHERE actor=? ORDER BY created DESC LIMIT 10",(actor,)).fetchall()
        labels={"WAITING_CODEX":"Codex 작업대기","CODEX_RUNNING":"Codex 수정중","REVIEW_REQUIRED":"초안 검토대기","NO_CHANGE":"수정 없음 · 검토필요","SCOPE_REJECTED":"범위 확인필요","CODEX_FAILED":"실행 실패 · 검토필요","CODEX_INTERRUPTED":"실행 중단 · 확인필요"}
        return "\n".join("#"+r[0]+" · "+labels.get(r[2],r[2])+" · "+r[1][:120] for r in rows) or "홈페이지 개선 대기 요청이 없습니다."

    def schedule_order_notices(self):
        active=set()
        with self.lock,sqlite3.connect(self.path) as c:
            for order in self.orders():
                state=order.get("display_state")
                delays={"PENDING_REVIEW":1800,"READY_TO_SHIP":3600,"AWAITING_DEPOSIT":86400}
                if state not in delays:continue
                key="order:"+str(order["order_id"])+":"+state;active.add(key)
                label={"PENDING_REVIEW":"주문 확인","READY_TO_SHIP":"배송 등록","AWAITING_DEPOSIT":"입금 상태 확인"}[state]
                body="주문 #"+str(order["order_id"])+" · "+label+" 대기\n"+order_identity(order)+"\n잊지 않도록 알려드립니다. ‘주문상세 #"+str(order["order_id"])+"’로 확인해 주세요."
                c.execute("INSERT OR IGNORE INTO dialogue_notices VALUES(?,'operations',?,'PENDING',?)",(key,body,self.clock()+delays[state]))
            for row in c.execute("SELECT id FROM dialogue_notices WHERE actor='operations' AND state='PENDING'").fetchall():
                if row[0] not in active:c.execute("UPDATE dialogue_notices SET state='CANCELLED' WHERE id=?",(row[0],))

    def notify_one(self, transport):
        self.schedule_order_notices()
        with self.lock,sqlite3.connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            now=self.clock()
            c.execute("UPDATE dialogue_notices SET state='CANCELLED' WHERE actor IN (SELECT actor FROM dialogue_sessions WHERE expires<?) AND state='PENDING'",(now,))
            row=c.execute("SELECT id,body FROM dialogue_notices WHERE state='PENDING' AND due<=? ORDER BY due LIMIT 1",(now,)).fetchone()
            if not row:return "IDLE"
            c.execute("UPDATE dialogue_notices SET state='CLAIMED' WHERE id=?",(row[0],))
        try:
            transport.send_message("안녕하세요 agachichi 입니다\n[개발]\n"+row[1]);state="SENT"
        except Exception:state="UNKNOWN"
        with sqlite3.connect(self.path) as c:c.execute("UPDATE dialogue_notices SET state=? WHERE id=?",(state,row[0]))
        return state
