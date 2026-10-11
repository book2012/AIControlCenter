"""Single-consumer forwarding adapter for separately pinned DEV releases."""
import re
import secrets
import time
from pathlib import Path
from core.shopping.operator_bridge import BridgeCodec, call_dev_bridge

DEV_SOCKET = Path("/Users/kyouhan/AIControlCenterRuntime/dev-order/data/operator-dev.sock")

def compose_dev_command_client(cfg, *, chat_id, user_ids, call=call_dev_bridge, clock=time.time):
    if set(cfg) != {"enabled", "environment", "hmac_key_hex"} or cfg.get("enabled") is not True or cfg.get("environment") != "DEV":
        raise ValueError("DEV_BRIDGE_CONFIGURATION_REQUIRED")
    if type(cfg.get("hmac_key_hex")) is not str or not re.fullmatch(r"[0-9a-f]{64}", cfg["hmac_key_hex"]):
        raise ValueError("DEV_BRIDGE_KEY_REQUIRED")
    if type(chat_id) is not int or not user_ids or any(type(v) is not int for v in user_ids):
        raise ValueError("DEV_BRIDGE_OPERATOR_REQUIRED")
    codec = BridgeCodec(bytes.fromhex(cfg["hmac_key_hex"]))
    def handle(text, update_id, actor):
        match = re.fullmatch(r"telegram-user-([0-9]+)", actor or "")
        if match is None or int(match[1]) not in user_ids:
            raise ValueError("OPERATOR_NOT_AUTHORIZED")
        body = dict(environment="DEV", update_id=update_id, chat_id=chat_id,
            user_id=int(match[1]), is_bot=False, text=text,
            timestamp=int(clock()), nonce=secrets.token_hex(16))
        # No retry or embedded old-release fallback after timeout/invalid receipt.
        return call(DEV_SOCKET, codec.sign(body), codec)
    return handle
