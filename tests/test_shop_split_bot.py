import sqlite3
from ops.macos.shopping.dev_split_bot import poll_once

def test_split_bot_authorization_namespace_and_no_replay(tmp_path):
    path=tmp_path/'cursor.db'
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE cursor(id INTEGER PRIMARY KEY,offset INTEGER)');c.execute('INSERT INTO cursor VALUES(1,0)')
    cfg={'operator_chat_id':10,'operator_user_ids':[20]};calls=[];sent=[]
    def update(i,user,text):return {'update_id':i,'message':{'chat':{'id':10,'type':'private'},'from':{'id':user,'is_bot':False},'text':text}}
    class Transport:
        def get_updates(self,offset):return [x for x in [update(1,21,'주문확인 #1'),update(2,20,'주문목록'),update(3,20,'주문확인 #1')] if x['update_id']>=offset]
        def send_message(self,text):sent.append(text)
    def client(text,i,actor):
        calls.append((text,i,actor))
        if '확인' in text:raise TimeoutError()
        return '개발 목록'
    poll_once(Transport(),client,cfg,path);poll_once(Transport(),client,cfg,path)
    assert calls==[('주문목록',(1<<60)+2,'telegram-user-20'),('주문확인 #1',(1<<60)+3,'telegram-user-20')]
    assert sent==['개발 목록']
    with sqlite3.connect(path) as c:assert c.execute('SELECT offset FROM cursor').fetchone()[0]==4
