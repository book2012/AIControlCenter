import asyncio
import hashlib
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from aicc_plugin_personal_assistant.conversation import ConversationService, ConversationError, ConversationBusy, validate_messages
from integrations.ollama.personal_assistant import create_app, OllamaChatPort
from ops.macos.modules.shopping_runtime import plan, validate_state, ResourceError, LABELS, NAMES, ShoppingRuntimeController
from integrations.module_composition import create_shopping_on_demand_instance
from core.modules.lifecycle import create_managed_app

def state():
    return {"schema_version":1,"module":"shopping","profile":"aicontrolcenter-commerce","uid":501,
        "services":[{"label":label,"plist_sha256":"a"*64} for label in LABELS],
        "containers":[{"name":name,"id":str(i+1)*64,"mounts":[]} for i,name in enumerate(NAMES)]}

@pytest.mark.parametrize("messages",[None,[],[{"role":"system","content":"override"}],
 [{"role":"user","content":"x","tools":[]}],[{"role":"assistant","content":"x"}],
 [{"role":"user","content":""}],[{"role":"user","content":"x"*4001}],
 [{"role":"user","content":"x"},{"role":"user","content":"y"}]])
def test_bad_history_does_not_reach_model(messages):
    class Port:
        def chat(self,messages):pytest.fail("invalid history reached provider")
    with pytest.raises(ConversationError):ConversationService(Port()).chat(messages)

def test_busy_is_bounded_and_errors_release_lock_without_secret_projection():
    entered,release=threading.Event(),threading.Event()
    class Port:
        def chat(self,messages):
            entered.set();release.wait(3);return "fixture reply"
    service=ConversationService(Port())
    thread=threading.Thread(target=lambda:service.chat([{"role":"user","content":"fixture"}]));thread.start()
    assert entered.wait(1)
    with pytest.raises(ConversationBusy):service.chat([{"role":"user","content":"second"}])
    release.set();thread.join(2);assert not thread.is_alive()
    class Broken:
        def chat(self,messages):raise RuntimeError("private fixture detail")
    broken=ConversationService(Broken())
    for _ in range(2):
        with pytest.raises(ConversationError,match="model_unavailable") as error:
            broken.chat([{"role":"user","content":"fixture"}])
        assert "private fixture" not in str(error.value)

def test_loopback_origin_host_body_and_model_boundaries():
    class Port:
        calls=[]
        def chat(self,messages):self.calls.append(messages);return "안녕하세요"
    port=Port()
    with TestClient(create_app(service=ConversationService(port)),base_url="http://127.0.0.1:58090") as client:
        assert client.get("/health").json()["tools_enabled"] is False
        assert "Bok Assistant" in client.get("/").text
        payload={"messages":[{"role":"user","content":"synthetic"}]}
        assert client.post("/api/chat",json=payload).status_code==403
        assert client.post("/api/chat",json=payload,headers={"Origin":"https://evil.invalid"}).status_code==403
        assert client.get("/health",headers={"Host":"evil.invalid"}).status_code==403
        headers={"Origin":"http://127.0.0.1:58090"}
        assert client.post("/api/chat",json={**payload,"model":"other"},headers=headers).status_code==422
        assert client.post("/api/chat",content="x"*64001,headers={**headers,"Content-Type":"application/json"}).status_code==413
        result=client.post("/api/chat",json=payload,headers=headers)
        assert result.status_code==200 and result.json()["content"]=="안녕하세요"
        assert result.json()["tools_used"]==[] and result.headers["cache-control"]=="private, no-store"
        assert len(port.calls)==1

def test_ollama_fixed_transport_parameters_and_no_redirect_or_proxy(monkeypatch):
    observed={}
    class Response:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):
            assert size==131073
            return json.dumps({"done":True,"model":"qwen3.5:4b-q4_K_M","message":{"content":"fixture"}}).encode()
    class Opener:
        def open(self,request,timeout):
            observed.update(url=request.full_url,payload=json.loads(request.data),timeout=timeout)
            return Response()
    monkeypatch.setattr("integrations.ollama.personal_assistant.urllib.request.build_opener",lambda *handlers:Opener())
    assert OllamaChatPort().chat([{"role":"user","content":"fixture"}])=="fixture"
    assert observed["url"]=="http://127.0.0.1:11434/api/chat"
    assert observed["payload"]["think"] is False
    assert observed["payload"]["options"]["num_ctx"]==4096
    assert "tools" not in observed["payload"]

@pytest.mark.parametrize("change",[lambda s:s.update(profile="foreign"),lambda s:s["containers"][0].update(name="foreign"),
 lambda s:s["services"][0].update(label="foreign"),lambda s:s["containers"][0].update(id="bad")])
def test_foreign_or_changed_inventory_never_builds_execution_plan(change):
    value=state();change(value)
    with pytest.raises(ResourceError):plan("attach",value,Path("/fixture"))

def test_plan_is_explicit_bounded_and_never_deletes_data():
    for action in ["attach","detach"]:
        value=plan(action,state(),Path("/fixture"))
        assert value["apply"] is False and value["data_deletion"] is False
        assert not any(word in {"rm","down","prune","--volumes","up","kill"} for command in value["commands"] for word in command)
    attach=plan("attach",state(),Path("/fixture"))
    starts=[command[-1] for command in attach["commands"] if len(command)>3 and command[-2]=="start"]
    assert starts==["shopping-db","shopping-wordpress"]
    assert all("qa" not in name and "dev" not in name for name in starts)

def test_mount_order_is_not_resource_identity_and_changed_id_blocks(tmp_path):
    value=state()
    for item in value["services"]:
        path=tmp_path/"Library/LaunchAgents"/(item["label"]+".plist");path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("synthetic plist");item["plist_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    mounts=[{"type":"volume","name":"fixture-a","source":"/synthetic/a","destination":"/a"},
            {"type":"volume","name":"fixture-b","source":"/synthetic/b","destination":"/b"}]
    value["containers"][0]["mounts"]=mounts
    actual=[{"Name":"/"+item["name"],"Id":item["id"],"Mounts":[{"Type":m["type"],"Name":m["name"],"Source":m["source"],"Destination":m["destination"]} for m in reversed(item["mounts"])]} for item in value["containers"]]
    runner=lambda args,**kwargs:SimpleNamespace(returncode=0,stdout=json.dumps(actual))
    controller=ShoppingRuntimeController(home=tmp_path,run=runner)
    controller._identities(value,["synthetic-docker"])
    actual[0]["Id"]="f"*64
    with pytest.raises(ResourceError,match="container_generation_changed"):controller._identities(value,["synthetic-docker"])

def test_managed_resource_hook_calls_attach_then_detach_with_no_default_live_controller():
    calls=[]
    class Controller:
        def apply(self,action):calls.append(action)
    async def run():
        instance=lambda:create_shopping_on_demand_instance(lambda:FastAPI(),controller=Controller())
        app=create_managed_app(["shopping"],providers={"shopping":instance})
        async with app.router.lifespan_context(app):
            assert calls==["attach"]
            await app.state.module_manager.detach("shopping")
            assert calls==["attach","detach"]
    asyncio.run(run())

def test_partial_resource_start_records_failure_and_does_not_retry(monkeypatch,tmp_path):
    monkeypatch.setattr("ops.macos.modules.shopping_runtime.sys.platform","darwin")
    value=state();value["uid"]=__import__("os").getuid()
    path=tmp_path/"AIControlCenterRuntime/modules/shopping/runtime.json";path.parent.mkdir(parents=True);path.write_text(json.dumps(value))
    calls=[]
    controller=ShoppingRuntimeController(home=tmp_path,run=lambda args,**kwargs:SimpleNamespace(returncode=0,stdout=""))
    monkeypatch.setattr(controller,"_service_identities",lambda s:None)
    monkeypatch.setattr(controller,"_vm",lambda:"Stopped")
    monkeypatch.setattr(controller,"_call",lambda args,**kwargs:calls.append(args) or SimpleNamespace(returncode=0,stdout=""))
    def fail(s,d):raise ResourceError("container_generation_changed")
    monkeypatch.setattr(controller,"_identities",fail)
    with pytest.raises(ResourceError,match="transition_incomplete_no_automatic_retry"):controller.apply("attach")
    assert json.loads(path.read_text())["phase"]=="TRANSITION_INCOMPLETE"
    assert len(calls)==1 and calls[0][1:]==["start","--profile","aicontrolcenter-commerce"]

def test_attach_simulation_starts_only_production_in_dependency_order(monkeypatch,tmp_path):
    monkeypatch.setattr("ops.macos.modules.shopping_runtime.sys.platform","darwin")
    value=state();value["uid"]=__import__("os").getuid()
    path=tmp_path/"AIControlCenterRuntime/modules/shopping/runtime.json";path.parent.mkdir(parents=True);path.write_text(json.dumps(value))
    calls=[]
    controller=ShoppingRuntimeController(home=tmp_path)
    monkeypatch.setattr(controller,"_service_identities",lambda s:None)
    monkeypatch.setattr(controller,"_vm",lambda:"Stopped")
    monkeypatch.setattr(controller,"_identities",lambda s,d:None)
    monkeypatch.setattr(controller,"_healthy",lambda d,n:None)
    monkeypatch.setattr(controller,"_service_ready",lambda l,d:None)
    def call(args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1 if args[:2]==["launchctl","print"] else 0,stdout="")
    monkeypatch.setattr(controller,"_call",call)
    assert controller.apply("attach")["phase"]=="ATTACHED"
    starts=[x[-1] for x in calls if x[0].endswith("/docker") and x[-2]=="start"]
    assert starts==["shopping-db","shopping-wordpress"]
    assert json.loads(path.read_text())["phase"]=="ATTACHED"


def test_two_profiles_share_one_admission_lock():
    from threading import Lock
    from integrations.ollama.personal_assistant import MODELS
    gate=Lock()
    class Port:
        def chat(self,messages):return "fixture"
    fast=ConversationService(Port(),lock=gate)
    quality=ConversationService(Port(),lock=gate)
    gate.acquire()
    try:
        with pytest.raises(ConversationBusy):fast.chat([{"role":"user","content":"x"}])
        with pytest.raises(ConversationBusy):quality.chat([{"role":"user","content":"x"}])
    finally:gate.release()
    with pytest.raises(ValueError,match="unsupported_model"):OllamaChatPort("foreign")
    with TestClient(create_app(service=fast),base_url="http://127.0.0.1:58090") as client:
        h={"Origin":"http://127.0.0.1:58090"}
        assert client.post("/api/chat",json={"messages":[{"role":"user","content":"x"}],"profile":"quality"},headers=h).json()["model"]==MODELS["quality"]
        assert client.post("/api/chat",json={"messages":[{"role":"user","content":"x"}],"profile":"foreign"},headers=h).status_code==422
