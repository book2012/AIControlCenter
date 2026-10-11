"""Authenticated private Unix-socket bridge; never polls or sends Telegram messages."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import socket
import socketserver
import threading
import time
from core.shopping.operator_environment import DurableOperatorEnvironmentRouter

MAX_FRAME = 16384

class BridgeDenied(ValueError):
    pass

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

class BridgeCodec:
    def __init__(self, key, *, clock=time.time):
        if type(key) is not bytes or len(key) != 32:
            raise BridgeDenied("BRIDGE_KEY_REQUIRED")
        self.key, self.clock = key, clock

    def sign(self, body):
        raw = canonical(body)
        return {"body": body, "mac": hmac.new(self.key, raw, hashlib.sha256).hexdigest()}

    def verify(self, envelope):
        if type(envelope) is not dict or set(envelope) != {"body", "mac"}:
            raise BridgeDenied("BRIDGE_ENVELOPE_INVALID")
        mac = envelope["mac"]
        if type(mac) is not str or not re.fullmatch(r"[0-9a-f]{64}", mac):
            raise BridgeDenied("BRIDGE_AUTH_DENIED")
        if not hmac.compare_digest(self.sign(envelope["body"])["mac"], mac):
            raise BridgeDenied("BRIDGE_AUTH_DENIED")
        return envelope["body"]

    def request(self, envelope):
        body = self.verify(envelope)
        keys = {"environment", "update_id", "chat_id", "user_id", "is_bot", "text", "timestamp", "nonce"}
        if type(body) is not dict or set(body) != keys:
            raise BridgeDenied("BRIDGE_REQUEST_INVALID")
        if body["environment"] != "DEV" or body["is_bot"] is not False:
            raise BridgeDenied("BRIDGE_TARGET_DENIED")
        if any(type(body[k]) is not int for k in ("update_id", "chat_id", "user_id", "timestamp")):
            raise BridgeDenied("BRIDGE_REQUEST_INVALID")
        if not 0 <= body["update_id"] < 2**63-1 or abs(self.clock()-body["timestamp"]) > 60:
            raise BridgeDenied("BRIDGE_REQUEST_EXPIRED")
        if type(body["nonce"]) is not str or not re.fullmatch(r"[0-9a-f]{32}", body["nonce"]):
            raise BridgeDenied("BRIDGE_REQUEST_INVALID")
        if type(body["text"]) is not str or not 1 <= len(body["text"]) <= 4096:
            raise BridgeDenied("BRIDGE_COMMAND_BOUNDS")
        return body

class DevOperatorBridge:
    def __init__(self, *, database_path, key, chat_id, user_ids, handler, clock=time.time):
        self.codec = BridgeCodec(key, clock=clock)
        self.lock = threading.Lock()
        self.handler = handler
        def denied(*_):
            raise BridgeDenied("BRIDGE_TARGET_DENIED")
        self.router = DurableOperatorEnvironmentRouter(database_path=database_path, dev=handler,
            prod=denied, default="DEV", chat_id=chat_id, user_ids=user_ids)

    def process(self, envelope):
        body = self.codec.request(envelope)
        environment, _ = self.router.target(body["text"], chat_id=body["chat_id"], user_id=body["user_id"])
        if environment != "DEV":
            raise BridgeDenied("BRIDGE_TARGET_DENIED")
        # The actor comes from the authenticated envelope; never a shared mutable global.
        def invoke(command, update_id):
            return self.handler(command, update_id, "telegram-user-"+str(body["user_id"]))
        with self.lock:
            self.router.handlers["DEV"] = invoke
            reply = self.router.dispatch(body["text"], chat_id=body["chat_id"],
                user_id=body["user_id"], update_id=body["update_id"])
        return self.codec.sign({"environment": "DEV", "nonce": body["nonce"],
            "update_id": body["update_id"], "reply": reply})

def read_frame(stream):
    raw = stream.readline(MAX_FRAME+1)
    if not raw.endswith(b"\n") or len(raw) > MAX_FRAME:
        raise BridgeDenied("BRIDGE_FRAME_BOUNDS")
    return json.loads(raw)

class PrivateBridgeServer:
    def __init__(self, path, bridge):
        self.path = Path(path)
        parent = self.path.parent
        if parent.is_symlink() or not parent.is_dir() or parent.stat().st_mode & 0o077:
            raise BridgeDenied("PRIVATE_BRIDGE_DIRECTORY_REQUIRED")
        if self.path.exists() or self.path.is_symlink():
            # Never unlink an unknown/live socket on startup.
            raise BridgeDenied("BRIDGE_SOCKET_EXISTS")
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                self.connection.settimeout(3)
                try:
                    response = bridge.process(read_frame(self.rfile))
                    self.wfile.write(canonical(response)+b"\n")
                except Exception:
                    self.wfile.write(b'{"error":"BRIDGE_REQUEST_DENIED"}\n')
        self.server = socketserver.UnixStreamServer(str(self.path), Handler)
        os.chmod(self.path, 0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.thread.join(5)
        self.server.server_close()
        self.path.unlink(missing_ok=True)

def call_dev_bridge(path, envelope, codec, *, timeout=30):
    """One attempt only. An unknown outcome must never trigger a command retry."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect(str(path))
        connection.sendall(canonical(envelope)+b"\n")
        with connection.makefile("rb") as stream:
            result = codec.verify(read_frame(stream))
    request = envelope["body"]
    if (type(result) is not dict or set(result) != {"environment", "nonce", "update_id", "reply"}
        or result["environment"] != "DEV" or result["nonce"] != request["nonce"]
        or type(result["update_id"]) is not int or result["update_id"] != request["update_id"]
        or type(result["reply"]) is not str or not 1 <= len(result["reply"]) <= 8192):
        raise BridgeDenied("BRIDGE_RECEIPT_INVALID")
    return result["reply"]
