"""One authorized Telegram consumer, explicit environment-bound command dispatch."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class OperatorTarget:
    environment: str
    handler: object

class OperatorEnvironmentRouter:
    def __init__(self,*,dev,prod,default,chat_id,user_ids):
        if default not in {"DEV","PROD"} or type(chat_id) is not int or not user_ids or any(type(v) is not int for v in user_ids):
            raise ValueError("OPERATOR_ROUTING_CONFIGURATION")
        if not callable(dev) or not callable(prod):raise ValueError("OPERATOR_HANDLERS_REQUIRED")
        self.handlers={"DEV":dev,"PROD":prod};self.default=default
        self.chat_id=chat_id;self.user_ids=frozenset(user_ids)
    def target(self,text,*,chat_id,user_id):
        if type(chat_id) is not int or type(user_id) is not int or chat_id!=self.chat_id or user_id not in self.user_ids:
            raise ValueError("OPERATOR_NOT_AUTHORIZED")
        if type(text) is not str or not text.strip() or len(text)>4096:raise ValueError("COMMAND_BOUNDS")
        text=text.strip();match=re.match(r"^(DEV|PROD|개발|운영)(?:\s+|:)(.*)$",text,re.S)
        environment=self.default
        if match:
            environment={"DEV":"DEV","PROD":"PROD","개발":"DEV","운영":"PROD"}[match[1]]
            text=match[2].strip()
        if not text:raise ValueError("EMPTY_COMMAND")
        # Resolve environment before any command parsing or mutation.
        return environment,text
    def dispatch(self,text,*,chat_id,user_id):
        environment,text=self.target(text,chat_id=chat_id,user_id=user_id)
        reply=self.handlers[environment](text)
        if type(reply) is not str:raise ValueError("OPERATOR_REPLY_INVALID")
        return "안녕하세요 agachichi 입니다\n["+("운영" if environment=="PROD" else "개발")+"]\n"+reply


class DurableOperatorEnvironmentRouter(OperatorEnvironmentRouter):
    """Pin each Telegram update to one environment before invoking a state-changing handler."""
    def __init__(self,*,database_path,**kwargs):
        super().__init__(**kwargs)
        from pathlib import Path
        import sqlite3,os
        self.path=Path(database_path)
        if self.path.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS environment_updates(update_id INTEGER PRIMARY KEY,digest TEXT NOT NULL,environment TEXT NOT NULL,state TEXT NOT NULL,reply TEXT)")
        os.chmod(self.path,0o600)
    def dispatch(self,text,*,chat_id,user_id,update_id):
        import sqlite3,hashlib,json
        environment,command=self.target(text,chat_id=chat_id,user_id=user_id)
        if type(update_id) is not int or update_id<0:raise ValueError("UPDATE_ID_REQUIRED")
        fingerprint=hashlib.sha256(json.dumps([chat_id,user_id,text],ensure_ascii=False).encode()).hexdigest()
        with sqlite3.connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT digest,environment,state,reply FROM environment_updates WHERE update_id=?",(update_id,)).fetchone()
            if row:
                if row[0]!=fingerprint:raise ValueError("UPDATE_CONFLICT")
                if row[2]=="COMPLETED":return row[3]
                raise ValueError("UPDATE_REQUIRES_INSPECTION")
            c.execute("INSERT INTO environment_updates VALUES(?,?,?,'CLAIMED',NULL)",(update_id,fingerprint,environment))
        # No automatic redispatch after a process interruption or ambiguous handler result.
        reply=self.handlers[environment](command,update_id)
        if type(reply) is not str:raise ValueError("OPERATOR_REPLY_INVALID")
        reply="안녕하세요 agachichi 입니다\n["+("운영" if environment=="PROD" else "개발")+"]\n"+reply
        with sqlite3.connect(self.path) as c:c.execute("UPDATE environment_updates SET state='COMPLETED',reply=? WHERE update_id=? AND state='CLAIMED'",(reply,update_id))
        return reply
