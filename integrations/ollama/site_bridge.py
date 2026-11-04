"""Outbound-only Site bridge for the existing loopback Qwen assistant."""
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse

SITE = "https://bok-personal-assistant.kyouhan.chatgpt.site"
NOTEBOOK_SITE = "https://bok-creative-notes.kyouhan.chatgpt.site"
LOCAL = "http://127.0.0.1:58090"
MODELS = {"fast": "qwen3.5:4b-q4_K_M", "quality": "qwen3.5:9b-q4_K_M"}
MODEL = MODELS["fast"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def load_config(path):
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError("private_config_required")
    value = json.loads(path.read_text())
    if value.get("site") not in {SITE, NOTEBOOK_SITE} or not isinstance(value.get("bridge_key"), str) or len(value["bridge_key"]) < 32:
        raise ValueError("invalid_config")
    if value["site"] == SITE and (not isinstance(value.get("site_access"), str) or len(value["site_access"]) < 32):
        raise ValueError("private_site_access_required")
    if value.get("site_access") and (not isinstance(value["site_access"], str) or len(value["site_access"]) < 32 or value.get("site_access_for", SITE) != value["site"]):
        raise ValueError("service_access_host_mismatch")
    return value

def request_json(url, *, payload=None, headers=None, timeout=15):
    target = urlparse(url)
    allowed = (target.scheme == "https" and target.netloc in {urlparse(SITE).netloc, urlparse(NOTEBOOK_SITE).netloc} and target.path == "/api/assistant/worker") or (target.scheme == "http" and target.netloc == "127.0.0.1:58090" and target.path in {"/health", "/api/chat", "/api/chat/stream"})
    if not allowed or target.query or target.fragment or target.username:
        raise ValueError("destination_denied")
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "AIControlCenter-QwenBridge/1.0", **(headers or {})})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(131073)
    if len(raw) > 131072:
        raise ValueError("oversized_response")
    return json.loads(raw)

def bridge_call(config, payload):
    site = config.get("site", SITE)
    if site not in {SITE, NOTEBOOK_SITE}:
        raise ValueError("destination_denied")
    headers = {"Authorization": "Bearer " + config["bridge_key"]}
    if config.get("site_access") and config.get("site_access_for", SITE) == site:
        headers["OAI-Sites-Authorization"] = "Bearer " + config["site_access"]
    return request_json(site + "/api/assistant/worker", payload=payload, headers=headers)

def local_ready():
    try:
        health = request_json(LOCAL + "/health", timeout=3)
        return health.get("model") == MODEL and health.get("tools_enabled") is False
    except Exception:
        return False

def process_job(job, on_progress=None):
    if not isinstance(job, dict) or not isinstance(job.get("messages"), list) or not 1 <= len(job["messages"]) <= 7:
        raise ValueError("invalid_job")
    if not isinstance(job.get("expiresAt"), (int, float)) or job["expiresAt"] < time.time() * 1000:
        raise ValueError("expired_job")
    profile = job.get("responseMode", "fast")
    if profile not in MODELS:
        raise ValueError("invalid_profile")
    if on_progress is not None:
        return process_stream(job, profile, on_progress)
    for attempt in range(4):
        try:
            response = request_json(LOCAL + "/api/chat", payload={"messages": job["messages"], "profile": profile},
                headers={"Origin": LOCAL}, timeout=100)
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(2)
    if response.get("model") != MODELS[profile] or response.get("provider") != "ollama-local" or response.get("tools_used") != []:
        raise ValueError("invalid_provider")
    content = response.get("content")
    if not isinstance(content, str) or not content.strip() or len(content) > 8000:
        raise ValueError("invalid_content")
    return content.strip()


def process_stream(job, profile, on_progress):
    payload={"messages":job["messages"],"profile":profile}
    request=urllib.request.Request(LOCAL+"/api/chat/stream",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","Origin":LOCAL,"User-Agent":"AIControlCenter-QwenBridge/1.0"})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    content,completed,size,last_update,updates="",False,0,0.0,0
    with opener.open(request,timeout=100) as response:
        while True:
            line=response.readline(16385)
            if not line:break
            size+=len(line)
            if len(line)>16384 or size>524288:raise ValueError("oversized_stream")
            item=json.loads(line)
            if item.get("error"):raise ValueError("model_unavailable")
            part=item.get("content","")
            if not isinstance(part,str):raise ValueError("invalid_content")
            content+=part
            if len(content)>8000:raise ValueError("invalid_content")
            now=time.monotonic()
            if part and content.strip() and updates<12 and (updates==0 or now-last_update>=.8):
                updates+=1;last_update=now
                try:on_progress(content,updates)
                except Exception:pass
            if item.get("done") is True:
                if item.get("model")!=MODELS[profile] or item.get("provider")!="ollama-local" or item.get("tools_used")!=[]:raise ValueError("invalid_provider")
                completed=True;break
    if not completed or not content.strip():raise ValueError("incomplete_stream")
    return content.strip()

def cycle(config):
    result = bridge_call(config, {"action": "claim", "ready": local_ready(), "model": MODEL})
    job = result.get("job")
    if not job:
        return False
    payload = {"action": "finish", "id": job["id"], "lease": job["lease"], "model": MODELS.get(job.get("responseMode", "fast"), MODEL)}
    try:
        if config.get("site",SITE)==NOTEBOOK_SITE:
            def progress(content,seq):
                bridge_call(config,{"action":"progress","id":job["id"],"lease":job["lease"],"content":content,"seq":seq})
            payload["content"]=process_job(job,on_progress=progress)
        else:
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
            delay = .25 if worked else (1 if config.get("site",SITE)==NOTEBOOK_SITE else 3)
        except Exception:
            status, delay = "connection_pending", 10
        if status != last_state:
            print(json.dumps({"service": "assistant-site-bridge", "state": status}), flush=True)
            last_state = status
        time.sleep(delay)

if __name__ == "__main__":
    main()
