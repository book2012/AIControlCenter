"""DEV inquiry escalation and explicitly approved FAQ reuse, not model fine tuning."""
import hashlib,json,os,re,secrets,sqlite3,time
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse

def sanitize(text):
    text=re.sub(r"(?:\+82[- .]?1[016789]|01[016789])[- .]?[0-9]{3,4}[- .]?[0-9]{4}","[연락처 제거]",text)
    text=re.sub(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}","[이메일 제거]",text)
    text=re.sub(r"https?://\S+","[링크 제거]",text)
    text=re.sub(r"[^\n]*(?:주소\s*[:：]|배송지\s*[:：]|수령인\s*[:：]|[가-힣]+(?:로|길)\s*[0-9]+|[0-9]+동\s*[0-9]+호)[^\n]*","[배송정보 제거]",text)
    return text.strip()[:1000]
def normalized(text):return " ".join(sanitize(text).lower().split())
def learning_safe(text):
    value=text.strip()
    if not value or sanitize(value)!=value:return False
    pii=r"(?:전화번호|휴대폰(?:\s*번호)?|핸드폰(?:\s*번호)?|연락처|이메일(?:\s*주소)?|주소|배송지|수령인|성함|이름|주민(?:등록)?번호|생년월일|계좌(?:번호)?|카드(?:번호)?|비밀번호|인증번호|OTP)"
    ask=r"(?:알려|입력|보내|남겨|제공|적어|기재|전달|말해|회신|작성)"
    if re.search(pii+r".{0,40}"+ask,value,re.I) or re.search(ask+r".{0,40}"+pii,value,re.I):return False
    if any(v in value for v in ("결제완료","결제 완료","주문확정 요청","주문 확정 요청")):return False
    return True
class DevInquiryQueue:
    def __init__(self,path,transport,clock=time.time):
        self.path=Path(path);self.transport=transport;self.clock=clock
        if self.path.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS inquiries(id TEXT PRIMARY KEY,token TEXT UNIQUE NOT NULL,product TEXT NOT NULL,question TEXT NOT NULL,answer TEXT,state TEXT NOT NULL,delivery TEXT NOT NULL,created REAL NOT NULL,answered REAL,approved REAL,message_id INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS inquiry_operator_updates(update_id INTEGER PRIMARY KEY,reply TEXT NOT NULL)")
        os.chmod(self.path,0o600)
    def lookup(self,product,question):
        q=normalized(question)
        with sqlite3.connect(self.path) as c:
            rows=c.execute("SELECT question,answer,approved FROM inquiries WHERE product=? AND state='APPROVED' AND approved>?",(product,self.clock()-30*86400)).fetchall()
        matches=[r for r in rows if normalized(r[0])==q]
        if not matches:return None
        return max(matches,key=lambda r:r[2])[1]
    def submit(self,product,question):
        q=sanitize(question);identifier=secrets.token_hex(4);token=secrets.token_hex(24)
        with sqlite3.connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT COUNT(*) FROM inquiries WHERE created>?",(self.clock()-60,)).fetchone()[0]>=10:raise ValueError("INQUIRY_RATE_LIMIT")
            if c.execute("SELECT COUNT(*) FROM inquiries WHERE created>?",(self.clock()-86400,)).fetchone()[0]>=100:raise ValueError("INQUIRY_DAILY_LIMIT")
            c.execute("INSERT INTO inquiries VALUES(?,?,?,?,NULL,'PENDING','PENDING',?,NULL,NULL,NULL)",(identifier,token,product,q,self.clock()))
        return {"inquiry_id":identifier,"inquiry_token":token}
    def dispatch_one(self):
        with sqlite3.connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE");r=c.execute("SELECT id,product,question FROM inquiries WHERE delivery='PENDING' ORDER BY created LIMIT 1").fetchone()
            if not r:return
            c.execute("UPDATE inquiries SET delivery='CLAIMED' WHERE id=?",(r[0],))
        try:
            receipt=self.transport.send_message("고객 문의 #"+r[0]+" · 상품 "+r[1]+"\n"+r[2]+"\n답장: 문의 #"+r[0]+" 답변 답변내용\n재사용 승인: 문의 #"+r[0]+" 학습승인\n개인정보·주문확정·결제 안내는 학습하지 않습니다.")
            with sqlite3.connect(self.path) as c:c.execute("UPDATE inquiries SET delivery='SENT',message_id=? WHERE id=?",(receipt,r[0]))
        except Exception:
            with sqlite3.connect(self.path) as c:c.execute("UPDATE inquiries SET delivery='UNKNOWN_OUTCOME' WHERE id=?",(r[0],))
    def command(self,text,update_id):
        m=re.fullmatch(r"문의\s*#([a-f0-9]{8})\s*(답변\s+(.{1,1000})|학습승인|학습제외)",text,re.S)
        if not m:return None
        with sqlite3.connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            old=c.execute("SELECT reply FROM inquiry_operator_updates WHERE update_id=?",(update_id,)).fetchone()
            if old:return old[0]
            row=c.execute("SELECT answer,state FROM inquiries WHERE id=?",(m[1],)).fetchone()
            reply="문의 번호를 찾지 못했습니다."
            if row:
                if m[3]:
                    answer=sanitize(m[3]);stamp=self.clock()
                    if not learning_safe(m[3]):
                        reply="개인정보 요청·인증·결제 민감 내용은 자동 학습할 수 없습니다."
                    else:
                        c.execute("UPDATE inquiries SET answer=?,state='APPROVED',answered=?,approved=? WHERE id=?",(answer,stamp,stamp,m[1]))
                        reply="문의 #"+m[1]+" 답변을 고객 화면에 전달했고 30일 자동 학습에 반영했습니다. 필요하면 학습제외해 주세요."
                elif m[2]=="학습승인":
                    if row[0] and row[1] in ("ANSWERED","APPROVED"):
                        c.execute("UPDATE inquiries SET state='APPROVED',approved=? WHERE id=?",(self.clock(),m[1]))
                        reply="문의 #"+m[1]+" 답변을 30일간 같은 상품의 같은 질문에 자동 응답합니다."
                    else:reply="먼저 답변을 등록해 주세요."
                else:
                    c.execute("UPDATE inquiries SET state='ANSWERED',approved=NULL WHERE id=?",(m[1],))
                    reply="문의 #"+m[1]+" 자동 응답에서 제외했습니다."
            c.execute("INSERT INTO inquiry_operator_updates VALUES(?,?)",(update_id,reply))
        return reply
    def admin_rows(self,limit=50):
        limit=max(1,min(int(limit),100))
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row
            rows=c.execute("SELECT id,product,question,answer,state,delivery,created,answered,approved FROM inquiries ORDER BY created DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) for r in rows]
    def status(self,token):
        if not re.fullmatch(r"[a-f0-9]{48}",token):return None
        with sqlite3.connect(self.path) as c:r=c.execute("SELECT answer,state FROM inquiries WHERE token=? AND created>?",(token,self.clock()-86400)).fetchone()
        if not r:return None
        return {"state":r[1],"answer":r[0]}
    def history_answer(self,token):
        if not re.fullmatch(r"[a-f0-9]{48}",token):return None
        with sqlite3.connect(self.path) as c:r=c.execute("SELECT answer FROM inquiries WHERE token=? AND created>?",(token,self.clock()-30*86400)).fetchone()
        return r[0] if r and r[0] else None
    def export(self,path):
        with sqlite3.connect(self.path) as c:rows=c.execute("SELECT product,question,answer FROM inquiries WHERE state='APPROVED' AND approved>?",(self.clock()-30*86400,)).fetchall()
        p=Path(path);p.write_text("".join(json.dumps({"product_id":r[0],"question":r[1],"answer":r[2]},ensure_ascii=False)+"\n" for r in rows));os.chmod(p,0o600)
        return len(rows)

def mount_inquiry_status(app,queue):
    @app.get("/__order-dev/chat/inquiries/{token}",include_in_schema=False)
    def status(token:str):
        value=queue.status(token)
        return JSONResponse(value or {"message":"문의 상태를 찾을 수 없습니다."},status_code=200 if value else 404,headers={"Cache-Control":"no-store"})
