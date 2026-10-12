"""Opt-in DEV-only command receiver. No Bot API polling, public route or PROD imports."""
import re
import sqlite3
from pathlib import Path
from core.shopping.operator_bridge import DevOperatorBridge, PrivateBridgeServer
from core.shopping.operator_intent import ALLOWED_LOCAL_MODELS

def compose_dev_bridge(*, cfg, data, telegram, adapter, products, conversation_cfg=None):
    if cfg.get("enabled") is not True:
        return None
    if set(cfg) != {"enabled", "environment", "hmac_key_hex"} or cfg["environment"] != "DEV":
        raise ValueError("DEV_BRIDGE_CONFIGURATION_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", cfg.get("hmac_key_hex", "")):
        raise ValueError("DEV_BRIDGE_KEY_REQUIRED")
    root = Path(data)
    if root.is_symlink() or root.stat().st_mode & 0o077:
        raise ValueError("PRIVATE_BRIDGE_DIRECTORY_REQUIRED")
    def handle(text, update_id, actor):
        reference = decision = reply = None
        if adapter is not None:
            reference, decision, reply = adapter.resolve(text, update_id=update_id,actor=actor)
        if reference is None and decision is None and reply is None:
            reply = products.command(text, update_id)
        match = re.fullmatch(r"/order_(status|confirm|reject) ([0-9a-f]{24})", text)
        if match:
            reference = match[2]
            decision = {"status": "STATUS", "confirm": "CONFIRMED", "reject": "REJECTED"}[match[1]]
        result={"outcome":"IGNORED"}
        if decision is not None:
            # The independent bot/bridge owns its own replay ledger and cursor.
            # Allocate a monotonically increasing local ledger operation ID;
            # never rewind the historical shared-bot cursor or advance it on reads.
            ledger_id=update_id
            offset=getattr(telegram._ledger,"telegram_offset",None)
            if callable(offset):ledger_id=max(ledger_id,offset())
            result=telegram._ledger.process_operator_update(ledger_id, reference=reference,
                decision=decision, actor_reference=actor,
                confirmation_guard=telegram._confirmation_guard)
        if reply:return reply
        if decision:
            outcome=result.get("outcome") if isinstance(result,dict) else "CONFIRMED"
            return "주문 상태: "+{"CONFIRMED":"확인완료 · 재고 차감 확인","ALREADY_CONFIRMED":"이미 확인완료","REJECTED":"거절","ALREADY_REJECTED":"이미 거절","STOCK_BLOCKED":"확정 보류 · 재고 확인 필요","CONFLICT":"현재 상태와 충돌 · 주문상세로 확인해 주세요.","NOT_FOUND":"해당 주문을 찾지 못했습니다.","DUPLICATE":"이미 처리한 메시지입니다. 주문상세로 확인해 주세요."}.get(outcome,str(outcome))
        return "상품관리 또는 주문목록으로 사용 가능한 명령을 확인해 주세요."
    conversation=None
    if conversation_cfg and conversation_cfg.get("enabled") is True:
        if conversation_cfg.get("environment")!="DEV" or conversation_cfg.get("model") not in ALLOWED_LOCAL_MODELS or adapter is None:
            raise ValueError("DEV_OPERATOR_CONVERSATION_CONFIGURATION_REQUIRED")
        from core.shopping.operator_intent import LocalOperatorJudge
        from core.shopping.operator_conversation import OperatorConversation
        from ops.macos.shopping.dev_product_operator import parse_command
        def execute_checked(text,update_id,actor):
            reply=handle(text,update_id,actor)
            try:product=parse_command(text,products.records)
            except ValueError:product=None
            if product and product.get("action") not in {"list","status","help"}:
                with sqlite3.connect("file:"+str(products.path.resolve())+"?mode=ro",uri=True) as c:
                    row=c.execute("SELECT state FROM product_commands WHERE update_id=?",(update_id,)).fetchone()
                if row and row[0]=="PENDING":raise RuntimeError("PRODUCT_OUTCOME_UNKNOWN")
            aftersales=adapter.aftersales
            cancelled=re.fullmatch(r"주문취소 #([1-9][0-9]*)",text)
            if cancelled and aftersales.cancellation(int(cancelled[1]))["state"] in {"SENDING","UNKNOWN"}:
                raise RuntimeError("CANCELLATION_OUTCOME_UNKNOWN")
            returned=re.fullmatch(r"반품 검수완료 #([a-f0-9]{8})",text)
            if returned:
                with sqlite3.connect("file:"+str(aftersales.path.resolve())+"?mode=ro",uri=True) as c:
                    row=c.execute("SELECT state FROM return_stock_operations WHERE case_id=?",(returned[1],)).fetchone()
                if row and row[0] in {"SENDING","UNKNOWN"}:raise RuntimeError("RETURN_OUTCOME_UNKNOWN")
            return reply
        judge_kwargs={}
        configured_model=conversation_cfg.get("model","qwen3:4b")
        configured_fallback=conversation_cfg.get("fallback_model")
        if configured_model != "qwen3:4b" or configured_fallback:
            judge_kwargs={"model":configured_model,"fallback_model":configured_fallback}
        conversation=OperatorConversation(path=root/"operator-dialogue.sqlite3",judge=LocalOperatorJudge(**judge_kwargs),
            orders=lambda:adapter.admin_orders(100),products=lambda:products.records,
            validate_product=lambda text:parse_command(text,products.records),executor=execute_checked)
    def conversational_handle(text,update_id,actor):
        if conversation is None or re.fullmatch(r"(?:문의\s*#[a-f0-9]{8}.*|/order_(?:status|confirm|reject) [0-9a-f]{24}|(?:환불|교환)(?:목록|(?:승인|거절)\s*#[a-f0-9]{8})|상품관리(?: 도움말)?|재고관리|/products)",text,re.S):
            return handle(text,update_id,actor)
        return conversation.handle(text,update_id,actor)
    bridge = DevOperatorBridge(database_path=root/"operator-bridge.sqlite3",
        key=bytes.fromhex(cfg["hmac_key_hex"]), chat_id=telegram._chat,
        user_ids=telegram._users, handler=conversational_handle)
    server=PrivateBridgeServer(root/"operator-dev.sock", bridge)
    server.conversation=conversation
    return server
