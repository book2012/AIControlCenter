from ops.macos.shopping.prod_order_buttons import callback_command, reply_markup

CFG={"operator_chat_id":-100123,"operator_user_ids":[501]}

def callback(data, text, *, username="mommychichi_bot", user_id=501):
    return {"update_id":99,"callback_query":{
        "id":"callback-id","data":data,"from":{"id":user_id,"is_bot":False},
        "message":{"text":text,"chat":{"id":-100123,"type":"private"},
                   "from":{"is_bot":True,"username":username}}}}

def test_menu_and_order_category_buttons():
    menu="안녕하세요 agachichi 입니다\n[운영]\n관리자 메뉴\n주문·상품 관리 작업을 선택하세요."
    markup=reply_markup(menu)
    assert markup["inline_keyboard"][0][0]["callback_data"]=="aiccp:menu:orders"
    selector="안녕하세요 agachichi 입니다\n[운영]\n주문 목록 보기를 선택해 주세요."
    markup=reply_markup(selector)
    assert markup["inline_keyboard"][0][0]["callback_data"]=="aiccp:orders:all:0"
    assert any(button["callback_data"]=="aiccp:orders:status:CANCELLED:0"
               for row in markup["inline_keyboard"] for button in row)

def test_order_card_buttons_are_bound_to_number_and_displayed_state():
    text=("안녕하세요 agachichi 입니다\n[운영]\n2610192105 · 01092838321 · 입금대기\n"
          "가격: 229000 KRW\n고객: 한경복 · 주문일: 2026-10-19 08:45\n- 상품 / S / 1개")
    markup=reply_markup(text)
    actions=[button["callback_data"] for button in markup["inline_keyboard"][0]]
    assert actions==["aiccp:item:detail:2610192105","aiccp:item:payment:2610192105","aiccp:item:cancel:2610192105"]
    assert callback_command(callback("aiccp:item:payment:2610192105",text),CFG)[2]=="01092838321 고객 입금 확인 #2610192105"
    assert callback_command(callback("aiccp:item:cancel:2610192105",text),CFG)[3]=="❌ 주문 취소 · 주문 #2610192105"

def test_callback_rejects_other_bot_user_and_stale_state():
    card="2610192105 · 01092838321 · 입금대기\n가격: 229000 KRW"
    assert callback_command(callback("aiccp:item:cancel:2610192105",card,username="papachichi_bot"),CFG) is None
    assert callback_command(callback("aiccp:item:cancel:2610192105",card,user_id=999),CFG) is None
    assert callback_command(callback("aiccp:item:payment:2610192105","2610192105 · 01092838321 · 배송중"),CFG) is None

def test_prod_transport_normalizes_environment_marker_without_network(monkeypatch):
    from pydantic import SecretStr
    from core.shopping.order_core.telegram import OrderTelegramTransport
    from ops.macos.shopping.prod_commerce_runtime import TaggedTransport
    monkeypatch.setattr(OrderTelegramTransport,"send_message",lambda self,text,reply_markup=None:text)
    transport=TaggedTransport(token=SecretStr("123:"+"x"*30),chat_id=-100123)
    reply=transport.send_message("안녕하세요 agachichi 입니다\n[개발]\n개발 전용 봇입니다.")
    assert "[운영]" in reply and "[개발]" not in reply and "개발" not in reply

def test_prod_transport_adds_operating_marker_to_legacy_greeting(monkeypatch):
    from pydantic import SecretStr
    from core.shopping.order_core.telegram import OrderTelegramTransport
    from ops.macos.shopping.prod_commerce_runtime import TaggedTransport
    monkeypatch.setattr(OrderTelegramTransport,"send_message",lambda self,text,reply_markup=None:text)
    transport=TaggedTransport(token=SecretStr("123:"+"x"*30),chat_id=-100123)
    reply=transport.send_message("안녕하세요 agachichi 입니다\n주문 상태입니다")
    assert reply.splitlines()[:2]==["안녕하세요 agachichi 입니다","[운영]"]

def test_order_results_are_sent_as_separate_cards_with_heading_and_button_context():
    from ops.macos.shopping.prod_order_buttons import send_reply
    class Transport:
        def __init__(self): self.messages=[]
        def send_message(self,text,reply_markup=None): self.messages.append((text,reply_markup))
    transport=Transport()
    text=("AICC_ORDER_PAGE:ALL:ALL:0:2:6\n전체 주문 6건 · 1/2\n"
          "2610192105 · 01092838321 · 입금대기\n가격: 229000 KRW\n고객: 한경복\n\n"
          "2610060072 · 01000000000 · 확인완료\n가격: 39000 KRW\n고객: DEV 고객")
    send_reply(transport,text,context="🔘 선택한 버튼: 📋 전체 보기")
    assert len(transport.messages)==3
    assert "전체 주문 6건 · 1/2" in transport.messages[0][0]
    assert "선택한 버튼: 📋 전체 보기" in transport.messages[0][0]
    assert "가격: 229000 KRW" in transport.messages[0][0]
    assert "가격: 39000 KRW" in transport.messages[1][0]
    assert "주문 더 보기" in transport.messages[2][0]
    assert transport.messages[0][1]["inline_keyboard"][0][0]["callback_data"]=="aiccp:item:detail:2610192105"
