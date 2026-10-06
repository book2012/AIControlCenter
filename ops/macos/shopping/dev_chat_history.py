"""Private DEV inquiry history; anonymous possession never authorizes customer history."""
from pathlib import Path
import hashlib,json,os,re,secrets,sqlite3,time
from fastapi import Request
from fastapi.responses import JSONResponse
COOKIE="__Host-aicc-chat"
class DevChatHistory:
    def __init__(self,path,authenticate,guest_customer_id,answer_lookup=None):
        self.path=Path(path);self.authenticate=authenticate;self.guest=guest_customer_id;self.answer_lookup=answer_lookup
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if self.path.is_symlink():raise ValueError("HISTORY_PATH")
        with self.db() as c:
            c.executescript("CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,owner TEXT,created REAL NOT NULL);CREATE TABLE IF NOT EXISTS turns(id INTEGER PRIMARY KEY,conversation TEXT NOT NULL,product TEXT NOT NULL,question TEXT NOT NULL,answer TEXT NOT NULL,action TEXT NOT NULL,created REAL NOT NULL);CREATE INDEX IF NOT EXISTS turns_conversation ON turns(conversation,created);")
            if "ticket" not in {row[1] for row in c.execute("PRAGMA table_info(turns)")}:c.execute("ALTER TABLE turns ADD COLUMN ticket TEXT")
        os.chmod(self.path,0o600)
    def db(self):return sqlite3.connect(self.path,timeout=10)
    def customer(self,request,write=False):
        auth=self.authenticate(request,write=write)
        if auth.customer_id!=self.guest:raise ValueError("PHONE_CUSTOMER_REQUIRED")
        return auth.customer_id
    def identifier(self,token):
        if not isinstance(token,str) or re.fullmatch(r"[a-f0-9]{64}",token) is None:raise ValueError("CHAT_TOKEN")
        return hashlib.sha256(token.encode()).hexdigest()
    def open(self,token,owner=None):
        try:
            key=self.identifier(token)
            with self.db() as c:row=c.execute("SELECT owner FROM conversations WHERE id=?",(key,)).fetchone()
            if row and (row[0] is None or row[0]==owner and owner is not None):return token
        except ValueError:pass
        token=secrets.token_hex(32)
        with self.db() as c:c.execute("INSERT INTO conversations VALUES(?,?,?)",(self.identifier(token),None,time.time()))
        return token
    def record(self,request,payload,result):
        try:key=self.identifier(request.cookies.get(COOKIE))
        except ValueError:return False
        try:owner=self.customer(request)
        except Exception:owner=None
        with self.db() as c:
            row=c.execute("SELECT owner FROM conversations WHERE id=?",(key,)).fetchone()
            if not row or row[0] is not None and row[0]!=owner:return False
            c.execute("DELETE FROM turns WHERE created<?",(time.time()-30*86400,))
            if c.execute("SELECT COUNT(*) FROM turns WHERE conversation=?",(key,)).fetchone()[0]>=200:return False
            c.execute("INSERT INTO turns(conversation,product,question,answer,action,created) VALUES(?,?,?,?,?,?)",(key,payload.product_id,payload.message,str(result["message"])[:2000],result["action"],time.time()))
            ticket=result.get("inquiry_token")
            if isinstance(ticket,str) and re.fullmatch(r"[a-f0-9]{48}",ticket):c.execute("UPDATE turns SET ticket=? WHERE id=last_insert_rowid()",(ticket,))
        return True
    def claim(self,token,owner):
        key=self.identifier(token)
        with self.db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT owner FROM conversations WHERE id=?",(key,)).fetchone()
            if not row or row[0] not in (None,owner):raise ValueError("CHAT_OWNER_DENIED")
            c.execute("UPDATE conversations SET owner=? WHERE id=?",(owner,key))
    def recent(self,owner):
        with self.db() as c:
            rows=c.execute("SELECT t.product,t.question,t.answer,t.action,t.created,t.ticket FROM turns t JOIN conversations c ON c.id=t.conversation WHERE c.owner=? AND t.created>=? ORDER BY t.id DESC LIMIT 30",(owner,time.time()-30*86400)).fetchall()
        items=[]
        for row in rows:
            item=dict(zip(("product_id","question","answer","action","created_at"),row[:5]))
            if row[5] and self.answer_lookup:
                answer=self.answer_lookup(row[5])
                if answer:item.update(answer=answer,action="OPERATOR_ANSWERED")
            items.append(item)
        return items
def mount_history(app,store):
    headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex"}
    @app.get("/__order-dev/chat/history/session",include_in_schema=False)
    def session(request:Request):
        try:owner=store.customer(request)
        except Exception:owner=None
        token=store.open(request.cookies.get(COOKIE),owner)
        response=JSONResponse({"ready":True},headers=headers)
        response.set_cookie(COOKIE,token,path="/",secure=True,httponly=True,samesite="strict")
        return response
    @app.post("/__order-dev/chat/history/link",include_in_schema=False)
    def link(request:Request):
        try:owner=store.customer(request,write=True);store.claim(request.cookies.get(COOKIE),owner)
        except Exception:return JSONResponse({"message":"휴대폰 인증 후 다시 확인해 주세요."},status_code=403,headers=headers)
        return JSONResponse({"linked":True},headers=headers)
    @app.get("/__order-dev/chat/history",include_in_schema=False)
    def recent(request:Request):
        try:owner=store.customer(request)
        except Exception:return JSONResponse({"message":"휴대폰 인증이 필요합니다."},status_code=401,headers=headers)
        return JSONResponse({"items":store.recent(owner)},headers=headers)
