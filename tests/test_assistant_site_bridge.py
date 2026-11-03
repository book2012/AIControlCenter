import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import pytest

SOURCE = Path(__file__).parents[1] / "integrations/ollama/site_bridge.py"
spec = importlib.util.spec_from_file_location("site_bridge", SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

def test_private_config_and_destination():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps({"site": bridge.SITE, "bridge_key": "a"*64, "site_access": "b"*64}))
        path.chmod(0o600)
        assert bridge.load_config(path)["site"] == bridge.SITE
        path.chmod(0o644)
        with pytest.raises(ValueError):
            bridge.load_config(path)
    with pytest.raises(ValueError):
        bridge.request_json("https://example.com/secret")

def test_job_uses_only_existing_local_conversation_api():
    job = {"messages": [{"role": "user", "content": "synthetic"}], "expiresAt": 9999999999999}
    with patch.object(bridge, "request_json", return_value={"model":bridge.MODEL,"provider":"ollama-local","tools_used":[],"content":"hello"}) as call:
        assert bridge.process_job(job) == "hello"
        assert call.call_args.args == (bridge.LOCAL + "/api/chat",)
        assert call.call_args.kwargs["headers"] == {"Origin": bridge.LOCAL}
    with patch.object(bridge, "request_json", return_value={"model":"other","provider":"ollama-local","tools_used":[],"content":"wrong"}):
        with pytest.raises(ValueError):
            bridge.process_job(job)

def test_failed_model_delivers_error_and_never_replays_model():
    job = {"id":"synthetic-id","lease":"synthetic-lease","messages":[]}
    calls = []
    def rpc(config, payload):
        calls.append(payload)
        if payload["action"] == "claim":
            return {"job": job}
        if len(calls) < 4:
            raise OSError()
        return {"ok":True}
    with patch.object(bridge,"bridge_call", side_effect=rpc), patch.object(bridge,"local_ready",return_value=True), patch.object(bridge,"process_job",side_effect=OSError()) as model, patch.object(bridge.time,"sleep"):
        assert bridge.cycle({}) is True
        assert model.call_count == 1
        assert calls[-1] == {"action":"finish","id":"synthetic-id","lease":"synthetic-lease","error":"model_unavailable"}

def test_local_health_rejects_tools_and_unknown_model():
    with patch.object(bridge,"request_json",return_value={"model":bridge.MODEL,"tools_enabled":True}):
        assert bridge.local_ready() is False


def test_public_notebook_profile_does_not_receive_private_site_access():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps({"site":bridge.NOTEBOOK_SITE,"bridge_key":"a"*64}))
        path.chmod(0o600)
        config=bridge.load_config(path)
        with patch.object(bridge,"request_json",return_value={"job":None}) as call:
            bridge.bridge_call(config,{"action":"claim","ready":True})
            assert call.call_args.args == (bridge.NOTEBOOK_SITE+"/api/assistant/worker",)
            assert "OAI-Sites-Authorization" not in call.call_args.kwargs["headers"]

def test_transport_rejects_other_paths_schemes_and_credential_urls():
    for url in [bridge.NOTEBOOK_SITE+"/mcp",bridge.NOTEBOOK_SITE.replace("https:","http:")+"/api/assistant/worker","http://127.0.0.1:58090/admin","https://user@bok-creative-notes.kyouhan.chatgpt.site/api/assistant/worker"]:
        with pytest.raises(ValueError): bridge.request_json(url)


def test_public_site_service_access_is_bound_to_its_exact_host():
    config={"site":bridge.NOTEBOOK_SITE,"bridge_key":"a"*64,"site_access":"notebook-token-"+"b"*64,"site_access_for":bridge.NOTEBOOK_SITE}
    with patch.object(bridge,"request_json",return_value={"job":None}) as call:
        bridge.bridge_call(config,{"action":"claim","ready":False})
        assert call.call_args.kwargs["headers"]["OAI-Sites-Authorization"]=="Bearer "+config["site_access"]
    config["site_access_for"]=bridge.SITE
    with patch.object(bridge,"request_json",return_value={"job":None}) as call:
        bridge.bridge_call(config,{"action":"claim","ready":False})
        assert "OAI-Sites-Authorization" not in call.call_args.kwargs["headers"]

def test_config_rejects_reusing_private_service_access_on_public_site():
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/"config.json"
        path.write_text(json.dumps({"site":bridge.NOTEBOOK_SITE,"bridge_key":"a"*64,"site_access":"b"*64}))
        path.chmod(0o600)
        with pytest.raises(ValueError):bridge.load_config(path)
