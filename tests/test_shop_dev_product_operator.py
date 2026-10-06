"""No external I/O: operator examples, authority, replay, read projection and SALE."""
from copy import deepcopy
import hashlib,json,sqlite3
from pathlib import Path
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from core.homepage.dev_test_stock import overlay,PATH
from core.homepage.dev_product_projection import apply_projection
from core.homepage.preview import create_app
from ops.macos.shopping.dev_product_operator import parse_command,CommandDenied,DevProductOperator,DevWooProductProvider,PHP
from core.shopping.order_core.telegram import OrderTelegramIntegration
from test_shop_order_001d_telegram import api,composed,clients,deny_network,Transport,CHAT,OPERATOR

SOURCE=PATH.with_name("dev-upload-products.json")
RECORDS=overlay(json.loads(SOURCE.read_text())["products"],SOURCE)
HASH=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
KNIT="ag-upload-top-0006"
BROWN="ag-upload-outer-0004"
CAMEL="ag-upload-outer-0001"

class Provider:
    def __init__(self):
        self.data={r["id"]:{"enabled":True,"regular_price":r["price"],"sale_price":None,"inventory":deepcopy(r["inventory"])} for r in RECORDS}
        self.receipts={};self.calls=[];self.fail_after_commit=False
    def snapshot(self):return deepcopy(self.data)
    def apply(self,cmd,uid,digest):
        self.calls.append(uid)
        if uid not in self.receipts:
            r=self.data[cmd["id"]];a=cmd["action"]
            if a=="stock":r["inventory"][cmd["key"]]=cmd["quantity"]
            elif a=="price":r["regular_price"]=cmd["amount"];r["sale_price"]=None
            elif a=="sale":
                if cmd["amount"]>=r["regular_price"]:raise CommandDenied("할인가를 정상 가격보다 낮게 입력해 주세요.")
                r["sale_price"]=cmd["amount"]
            elif a=="unsale":r["sale_price"]=None
            elif a=="hide":r["enabled"]=False
            elif a=="show":r["enabled"]=True
            self.receipts[uid]=digest
            if self.fail_after_commit:self.fail_after_commit=False;raise TimeoutError()
        assert self.receipts[uid]==digest
        return self.snapshot()

def operator(tmp_path,provider=None):
    return DevProductOperator(records=RECORDS,provider=provider or Provider(),path=tmp_path/"commands.sqlite3",projection_path=tmp_path/"projection.json",catalog_hash=HASH)

@pytest.mark.parametrize("text,expected",[
 ("카멜 벨티드 롱 코트 L는 재고 없음으로 변경",{"action":"stock","id":CAMEL,"key":"L","quantity":0}),
 ("브라운 싱글 롱 코트 가격 200000원으로 변경",{"action":"price","id":BROWN,"amount":200000}),
 ("베이직 하이넥 니트 는 50000으로 할인",{"action":"sale","id":KNIT,"amount":50000}),
 ("베이직 하이넥 니트 네이비 M 재고 3개로 변경",{"action":"stock","id":KNIT,"key":"navy--m","quantity":3}),
 ("브라운 싱글 롱 코트 삭제",{"action":"hide","id":BROWN}),
 ("브라운 싱글 롱 코트 다시 공개",{"action":"show","id":BROWN}),
 ("베이직 하이넥 니트 할인 취소",{"action":"unsale","id":KNIT}),
])
def test_examples(text,expected):assert parse_command(text,RECORDS)==expected

@pytest.mark.parametrize("text",[
 "베이직 하이넥 니트 L 재고 없음","카멜 벨티드 롱 코트 재고 3개",
 "베이직 하이넥 니트 네이비 M L 재고 3개","베이직 하이넥 니트 빨강 M 재고 3개",
 "브라운 싱글 롱 코트 가격 -1원","브라운 싱글 롱 코트 가격 20,00원",
 "브라운 싱글 롱 코트 가격 0원","새로운 상품 추가",
 "브라운 싱글 롱 코트 가격 200000원으로 변경 그리고 삭제",
])
def test_ambiguous_or_invalid_commands_deny_without_write(tmp_path,text):
    op=operator(tmp_path);assert op.command(text,1);assert not op.provider.calls
    assert not op.projection_path.exists()

def test_replay_restart_and_receipt_conflict(tmp_path):
    op=operator(tmp_path);text="브라운 싱글 롱 코트 가격 200000원으로 변경"
    reply=op.command(text,100);assert "200,000" in reply and op.provider.calls==[100]
    assert operator(tmp_path,op.provider).command(text,100)==reply
    assert op.provider.calls==[100]
    with pytest.raises(ValueError,match="REPLAY_CONFLICT"):op.command("브라운 싱글 롱 코트 숨김",100)

def test_uncertain_provider_commit_recovers_same_key_without_second_mutation(tmp_path):
    op=operator(tmp_path);op.provider.fail_after_commit=True
    assert "재확인" in op.command("카멜 벨티드 롱 코트 L 재고 없음",20)
    assert op.provider.data[CAMEL]["inventory"]["L"]==0
    restarted=operator(tmp_path,op.provider)
    assert "0개" in restarted.recover()[0]
    assert op.provider.calls==[20,20] and len(op.provider.receipts)==1
    assert json.loads(op.projection_path.read_text())["products"][CAMEL]["inventory"]["L"]==0

def test_sale_hide_restore_and_stock_reflect_without_app_restart(tmp_path):
    op=operator(tmp_path);op.sync()
    with TestClient(create_app(managed_projection=op.projection_path)) as client:
        assert client.get("/homepage/storefront?collection=sale").status_code==200
        assert 'href="/homepage/storefront/product/'+KNIT not in client.get("/homepage/storefront?collection=sale").text
        op.command("베이직 하이넥 니트 50000으로 할인",1)
        sale=client.get("/homepage/storefront?collection=sale").text
        assert KNIT in sale and "#SALE" in sale
        detail=client.get("/homepage/storefront/product/"+KNIT).text
        assert "SALE · 정상가 69,000원" in detail
        op.command("브라운 싱글 롱 코트 가격 200000원으로 변경",2)
        assert "200,000원" in client.get("/homepage/storefront/product/"+BROWN).text
        op.command("카멜 벨티드 롱 코트 L 재고 없음",3)
        variants=client.get("/shopping/products/"+CAMEL).json()["variants"]
        assert next(v for v in variants if v["label"]=="L")["available"] is False
        before=deepcopy(op.provider.data[BROWN])
        op.command("브라운 싱글 롱 코트 제거",4)
        assert client.get("/homepage/storefront/product/"+BROWN).status_code==404
        assert 'href="/homepage/storefront/product/'+BROWN not in client.get("/homepage/storefront?collection=hot").text
        assert client.get("/shopping/products?page_size=100").json()["total"]==18
        op.command("브라운 싱글 롱 코트 다시 공개",5)
        assert client.get("/homepage/storefront/product/"+BROWN).status_code==200
        assert op.provider.data[BROWN]==before
        op.command("베이직 하이넥 니트 할인 취소",6)
        assert 'href="/homepage/storefront/product/'+KNIT not in client.get("/homepage/storefront?collection=sale").text
        assert "69,000원" in client.get("/homepage/storefront/product/"+KNIT).text

@pytest.mark.parametrize("kind",["prod","hash","extra","negative","sale","unknown_option"])
def test_projection_boundaries(tmp_path,kind):
    op=operator(tmp_path);op.sync();data=json.loads(op.projection_path.read_text())
    if kind=="prod":data["environment"]="PROD"
    if kind=="hash":data["catalog_sha256"]="0"*64
    if kind=="extra":data["products"]["unknown"]=data["products"][KNIT]
    if kind=="negative":data["products"][KNIT]["inventory"]["navy--m"]=-1
    if kind=="sale":data["products"][KNIT]["sale_price"]=999999
    if kind=="unknown_option":data["products"][KNIT]["inventory"]["green--m"]=3
    with pytest.raises(ValueError):apply_projection(RECORDS,data,HASH)

def test_corrupt_projection_fails_closed_then_recovers(tmp_path):
    op=operator(tmp_path);op.sync()
    with TestClient(create_app(managed_projection=op.projection_path)) as client:
        assert client.get("/shopping/products?page_size=100").json()["total"]==19
        op.projection_path.write_text('{"environment":"PROD"}')
        assert client.get("/shopping/products?page_size=100").json()["total"]==0
        op.sync()
        assert client.get("/shopping/products?page_size=100").json()["total"]==19

@pytest.mark.parametrize("change",[{"chat":CHAT+1},{"user":OPERATOR+1},{"bot":True},{"type":"group"},{"type":"supergroup"}])
def test_product_commands_only_trusted_private_operator(api,composed,change):
    _,ledger,_=composed;t=Transport();op=Mock()
    msg={"chat":{"id":change.get("chat",CHAT),"type":change.get("type","private")},"from":{"id":change.get("user",OPERATOR),"is_bot":change.get("bot",False)},"text":"브라운 싱글 롱 코트 숨김"}
    t.updates=[{"update_id":1,"message":msg}]
    integration=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),product_operator=op)
    integration.poll_once();op.command.assert_not_called();assert t.messages==[]

def test_trusted_update_routes_and_duplicate_does_not_reapply(api,composed,tmp_path):
    _,ledger,_=composed;t=Transport();op=operator(tmp_path)
    t.updates=[{"update_id":1,"message":{"chat":{"id":CHAT,"type":"private"},"from":{"id":OPERATOR,"is_bot":False},"text":"브라운 싱글 롱 코트 숨김"}}]
    tg=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),product_operator=op)
    tg.poll_once();tg.poll_once()
    assert op.provider.calls==[1] and len(t.messages)==1 and "숨김 완료" in t.messages[0]

def test_provider_options_default_size_and_hardwired_dev_boundary():
    bindings=[{"demo_id":r["id"],"product_id":i+1,"sku":"aicc-dev-"+r["id"]} for i,r in enumerate(RECORDS)]
    p=DevWooProductProvider(records=RECORDS,bindings=bindings,assert_isolation=Mock())
    assert next(r for r in p.rows if r["id"]==CAMEL)["options"]["L"]=={"size":"L"}
    assert "WORDPRESS_DB_NAME" in PHP and "aicc_order_dev" in PHP and "aicc_dev_stock_confirmation" in PHP
    assert "wp_delete_post" not in PHP and "->delete(" not in PHP

def test_hidden_provider_product_is_denied_before_variation_read():
    from ops.macos.shopping.dev_order_runtime import DevCatalog
    class Hidden(DevCatalog):
        def read(self,path):
            assert "/variations" not in path
            return {"id":1,"sku":"aicc-dev-test","status":"draft"}
    cat=Hidden({},{"active_products":[{"product_id":1,"demo_id":BROWN,"sku":"aicc-dev-test","category":"OUTER"}]})
    with pytest.raises(ValueError,match="DEV_PRODUCT_BINDING"):cat.get_product("1")

def test_existing_inquiry_reply_with_price_words_precedes_product_parser(api,composed):
    _,ledger,_=composed;t=Transport();product_op=Mock();existing=Mock()
    existing.resolve.return_value=(None,None,"문의 답변 저장")
    text="문의답변 #123 가격 할인 문의를 확인했습니다"
    t.updates=[{"update_id":1,"message":{"chat":{"id":CHAT,"type":"private"},"from":{"id":OPERATOR,"is_bot":False},"text":text}}]
    tg=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),operator_adapter=existing,product_operator=product_op)
    tg.poll_once();product_op.command.assert_not_called()
    assert t.messages==["문의 답변 저장"]

@pytest.mark.parametrize("text",["아우터 리스트","아우터 목록","아우터리스트","  아우터   리스트  "])
def test_outer_list_reads_current_stock_and_hidden_state_without_mutation(tmp_path,text):
    op=operator(tmp_path)
    op.provider.data[CAMEL]["inventory"]["L"]=0
    op.provider.data[BROWN]["enabled"]=False
    reply=op.command(text,99)
    assert "[DEV] 아우터 재고 · 5개 상품" in reply
    assert "카멜 벨티드 롱 코트" in reply and "L: 품절 (0개)" in reply
    assert "브라운 싱글 롱 코트 [숨김]" in reply
    assert "브라운 / M: 3개" in reply
    assert "베이직 하이넥 니트" not in reply
    assert len(reply)<4096 and not op.provider.calls
    with sqlite3.connect(op.path) as c:assert c.execute("SELECT COUNT(*) FROM product_commands").fetchone()[0]==0

def test_outer_list_trusted_telegram_reply_and_duplicate(api,composed,tmp_path):
    _,ledger,_=composed;t=Transport();op=operator(tmp_path)
    t.updates=[{"update_id":1,"message":{"chat":{"id":CHAT,"type":"private"},"from":{"id":OPERATOR,"is_bot":False},"text":"아우터 리스트"}}]
    tg=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),product_operator=op)
    tg.poll_once();tg.poll_once()
    assert len(t.messages)==1 and "카멜 벨티드 롱 코트" in t.messages[0]
    assert not op.provider.calls

def test_outer_list_empty_category_is_truthful(tmp_path):
    op=operator(tmp_path);op.records=[r for r in RECORDS if r["category"]!="outer"]
    op.provider.data={r["id"]:op.provider.data[r["id"]] for r in op.records}
    assert op.command("아우터 리스트",1)=="[DEV] 등록된 아우터가 없습니다."

def test_outer_list_displays_regular_price_and_sale_before_after(tmp_path):
    op=operator(tmp_path)
    op.provider.data[BROWN]["regular_price"]=200000
    op.provider.data[BROWN]["sale_price"]=150000
    reply=op.command("아우터 리스트",1)
    block=next(b for b in reply.split("\n\n") if b.startswith("브라운 싱글 롱 코트"))
    assert "SALE · 정상가 200,000원 → 할인가 150,000원" in block
    assert "브라운 / M: 3개" in block
    assert "가격 300,000원 · 세일 아님" in reply
    assert len(reply)<4096 and not op.provider.calls

def test_outer_list_uses_latest_price_after_sale_cancellation(tmp_path):
    op=operator(tmp_path)
    op.provider.data[BROWN]["sale_price"]=100000
    assert "할인가 100,000원" in op.command("아우터 리스트",1)
    op.provider.data[BROWN]["sale_price"]=None
    op.provider.data[BROWN]["regular_price"]=200000
    reply=op.command("아우터 리스트",2)
    block=next(b for b in reply.split("\n\n") if b.startswith("브라운 싱글 롱 코트"))
    assert "가격 200,000원 · 세일 아님" in block and "할인가" not in block
    assert not op.provider.calls
