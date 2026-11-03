"""Outbound-only Site bridge for the existing loopback Qwen assistant."""
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
import time
import urllib.request
from urllib.parse import urlparse

SITE = "https://bok-personal-assistant.kyouhan.chatgpt.site"
LOCAL = "http://127.0.0.1:58090"
MODEL = "qwen3:8b"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def load_config(path):
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError("private_config_required")
    value = json.loads(path.read_text())
    if value.get("site") != SITE or any(not isinstance(value.get(k), str) or len(value[k]) < 32 for k in ("bridge_key", "site_access")):
        raise ValueError("invalid_config")
    return value

def request_json(url, *, payload=None, headers=None, timeout=15):
    if urlparse(url).netloc not in {urlparse(SITE).netloc, "127.0.0.1:58090"}:
        raise ValueError("destination_denied")
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(131073)
    if len(raw) > 131072:
        raise ValueError("oversized_response")
    return json.loads(raw)

def bridge_call(config, payload):
    return request_json(SITE + "/api/assistant/worker", payload=payload, headers={
        "Authorization": "Bearer " + config["bridge_key"],
        "OAI-Sites-Authorization": "Bearer " + config["site_access"],
    })

def local_ready():
    try:
        health = request_json(LOCAL + "/health", timeout=3)
        return health.get("model") == MODEL and health.get("tools_enabled") is False
    except Exception:
        return False

def process_job(job):
    if not isinstance(job, dict) or not isinstance(job.get("messages"), list) or not 1 <= len(job["messages"]) <= 7:
        raise ValueError("invalid_job")
    if not isinstance(job.get("expiresAt"), (int, float)) or job["expiresAt"] < time.time() * 1000:
        raise ValueError("expired_job")
    response = request_json(LOCAL + "/api/chat", payload={"messages": job["messages"]},
        headers={"Origin": LOCAL}, timeout=100)
    if response.get("model") != MODEL or response.get("provider") != "ollama-local" or response.get("tools_used") != []:
        raise ValueError("invalid_provider")
    content = response.get("content")
    if not isinstance(content, str) or not content.strip() or len(content) > 8000:
        raise ValueError("invalid_content")
    return content.strip()

def cycle(config):
    result = bridge_call(config, {"action": "claim", "ready": local_ready()})
    job = result.get("job")
    if not job:
        return False
    payload = {"action": "finish", "id": job["id"], "lease": job["lease"]}
    try:
        payload["content"] = process_job(job)
    except Exception:
        payload["error"] = "model_unavailable"
    # Retry delivery only. Never run the model a second time for a claimed job.
    for attempt in range(3):
        try:
            bridge_call(config, payload)
            return True
        except Exception:
            if attempt == 2:
                raise RuntimeError("result_delivery_failed") from None
            time.sleep(2)
    return True

def main():
    path = Path(sys.argv[1])
    config = load_config(path)
    lock = path.with_suffix(".lock").open("a")
    os.chmod(lock.name, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    last_state = None
    while True:
        try:
            worked = cycle(config)
            status = "connected"
            delay = 1 if worked else 3
        except Exception:
            status, delay = "connection_pending", 10
        if status != last_state:
            print(json.dumps({"service": "assistant-site-bridge", "state": status}), flush=True)
            last_state = status
        time.sleep(delay)

if __name__ == "__main__":
    main()
