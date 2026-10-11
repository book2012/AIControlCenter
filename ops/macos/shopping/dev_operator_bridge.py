"""Opt-in DEV-only command receiver. No Bot API polling, public route or PROD imports."""
import re
from pathlib import Path
from core.shopping.operator_bridge import DevOperatorBridge, PrivateBridgeServer

def compose_dev_bridge(*, cfg, data, telegram, adapter, products):
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
            reference, decision, reply = adapter.resolve(text, update_id=update_id)
        if reference is None and decision is None and reply is None:
            reply = products.command(text, update_id)
        match = re.fullmatch(r"/order_(status|confirm|reject) ([0-9a-f]{24})", text)
        if match:
            reference = match[2]
            decision = {"status": "STATUS", "confirm": "CONFIRMED", "reject": "REJECTED"}[match[1]]
        telegram._ledger.process_operator_update(update_id, reference=reference,
            decision=decision, actor_reference=actor if decision else None,
            confirmation_guard=telegram._confirmation_guard)
        return reply or ("주문 상태를 반영했습니다. 주문목록으로 확인해 주세요." if decision
            else "상품관리 또는 주문목록으로 사용 가능한 명령을 확인해 주세요.")
    bridge = DevOperatorBridge(database_path=root/"operator-bridge.sqlite3",
        key=bytes.fromhex(cfg["hmac_key_hex"]), chat_id=telegram._chat,
        user_ids=telegram._users, handler=handle)
    return PrivateBridgeServer(root/"operator-dev.sock", bridge)
