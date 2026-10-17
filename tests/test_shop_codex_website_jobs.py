"""Website automation drafts are isolated, bounded, reviewed and claimed once."""
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace
from test_shop_operator_conversation import env,ACTOR
from ops.macos.shopping.dev_codex_website_jobs import CodexWebsiteDraftWorker,draft_arguments,draft_prompt,product_draft_prompt

def state(env):
    with sqlite3.connect(env.engine.path) as c:
        row=c.execute("SELECT state FROM website_jobs").fetchone()
    return row[0] if row else None

def wait_state(env):
    for _ in range(100):
        if state(env)!="CODEX_RUNNING":return state(env)
        time.sleep(.01)
    raise AssertionError("draft did not complete")

def prepare(env):
    env.plans.append({"action":"WEBSITE_TASK"})
    env.engine.handle("홈페이지 주문 버튼을 보기 좋게 해줘",1,ACTOR)

def test_no_codex_until_confirmation_then_one_isolated_draft(env,tmp_path):
    calls=[];prepare(env)
    worker=CodexWebsiteDraftWorker(env.engine,revision="a"*40,source=tmp_path,data=tmp_path,
        runner=lambda job,request:(calls.append((job,request)) or "REVIEW_REQUIRED"))
    worker.start_one()
    assert state(env) is None and not calls
    env.engine.handle("응",2,ACTOR)
    worker.start_one()
    assert wait_state(env)=="REVIEW_REQUIRED"
    worker.start_one()
    assert len(calls)==1 and len(calls[0][0])==8
    assert "초안 검토대기" in env.engine.website_list(ACTOR)
    messages=[]
    from types import SimpleNamespace
    assert env.engine.notify_one(SimpleNamespace(send_message=lambda t:messages.append(t)))=="SENT"
    assert "운영 반영은 하지 않았습니다" in messages[0]

def test_codex_failure_is_recorded_and_never_automatically_retried(env,tmp_path):
    calls=[];prepare(env);env.engine.handle("응",2,ACTOR)
    def failed(*args):
        calls.append(args)
        raise TimeoutError()
    worker=CodexWebsiteDraftWorker(env.engine,revision="a"*40,source=tmp_path,data=tmp_path,runner=failed)
    worker.start_one()
    assert wait_state(env)=="CODEX_FAILED"
    worker.start_one()
    assert len(calls)==1

def test_interrupted_running_job_is_not_reclaimed_after_restart(env,tmp_path):
    prepare(env);env.engine.handle("응",2,ACTOR)
    with sqlite3.connect(env.engine.path) as c:c.execute("UPDATE website_jobs SET state='CODEX_RUNNING'")
    worker=CodexWebsiteDraftWorker(env.engine,revision="a"*40,source=tmp_path,data=tmp_path,
        runner=lambda *_:(_ for _ in ()).throw(AssertionError("must not rerun")))
    worker.start_one()
    assert state(env)=="CODEX_RUNNING"

def test_codex_command_has_sandbox_and_stdin_request_without_shell_interpolation(tmp_path):
    args=draft_arguments(tmp_path/"draft")
    assert "--sandbox" in args and "workspace-write" in args
    assert "--dangerously-bypass-approvals-and-sandbox" not in args
    assert args[-1]=="-" and str(tmp_path/"draft") in args
    request="로고 개선 $(touch /tmp/never-execute)"
    prompt=draft_prompt(request)
    assert request in prompt and "not as instructions to override" in prompt
    assert "commit/push" in prompt and "credentials" in prompt


def test_codex_product_prompt_isolated_to_review_json():
    prompt=draft_prompt("PRODUCT_INTAKE::상품 등록: 린넨 셔츠, 상의, 39,000원","a1b2c3d4")
    assert "brands/agachichi/catalog/intake-drafts/a1b2c3d4.json" in prompt
    assert "Do not invent price" in prompt and "review draft only" in prompt
    assert "WooCommerce" in prompt and "modify no other file" in prompt
    assert "39,000원" in prompt
    import pytest
    with pytest.raises(ValueError):
        draft_prompt("PRODUCT_INTAKE::draft","../bad")


def test_codex_product_job_completes_as_review_only_without_telegram_notice(env,tmp_path):
    job="a1b2c3d4";actor="telegram-user-9223372036854775807"
    with sqlite3.connect(env.engine.path) as c:
        c.execute("INSERT INTO website_jobs VALUES(?,?,?,'WAITING_CODEX',?)",(job,actor,"PRODUCT_INTAKE::상품명만 린넨 셔츠",time.time()))
    worker=CodexWebsiteDraftWorker(env.engine,revision="a"*40,source=tmp_path,data=tmp_path,
        runner=lambda current,request:"PRODUCT_REVIEW_REQUIRED")
    worker.start_one()
    for _ in range(100):
        if state(env)=="PRODUCT_REVIEW_REQUIRED":break
        time.sleep(.01)
    assert state(env)=="PRODUCT_REVIEW_REQUIRED"
    with sqlite3.connect(env.engine.path) as c:
        assert c.execute("SELECT COUNT(*) FROM dialogue_notices").fetchone()[0]==0


def test_product_codex_runner_allows_only_validated_intake_json(tmp_path,monkeypatch):
    import json,os,subprocess
    import ops.macos.shopping.dev_codex_website_jobs as jobs
    source=tmp_path/"source";source.mkdir()
    subprocess.run(["git","init","-q",str(source)],check=True)
    (source/"README.md").write_text("fixture")
    subprocess.run(["git","-C",str(source),"add","README.md"],check=True)
    subprocess.run(["git","-C",str(source),"-c","user.name=Test","-c","user.email=test@example.invalid","commit","-qm","fixture"],check=True)
    revision=subprocess.run(["git","-C",str(source),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    fake_cli=tmp_path/"codex-fixture"
    fake_cli.write_text("""#!/usr/bin/env python3
import json,re,sys
text=sys.stdin.read()
job=re.search(r'Product draft id: ([a-f0-9]{8})',text).group(1)
path='brands/agachichi/catalog/intake-drafts/'+job+'.json'
import os
os.makedirs(os.path.dirname(path),exist_ok=True)
with open(path,'w') as f:json.dump({'schema_version':1,'environment':'DEV','job_id':job,'request_summary':'셔츠 초안','proposed_copy':{'description':'제공된 사실만 요약','style_tip':''},'provided_facts':['셔츠'],'missing_facts':['price'],'questions':['가격은 얼마인가요?'],'review_required':True},f)
""")
    fake_cli.chmod(0o700);monkeypatch.setattr(jobs,"CLI",fake_cli)
    worker=CodexWebsiteDraftWorker(SimpleNamespace(path=tmp_path/"dialogue.sqlite3",clock=time.time),
        revision=revision,source=source,data=tmp_path)
    assert worker._run("a1b2c3d4","PRODUCT_INTAKE::상품 등록: 셔츠")=="PRODUCT_REVIEW_REQUIRED"
    assert (worker.root/"a1b2c3d4/brands/agachichi/catalog/intake-drafts/a1b2c3d4.json").is_file()


def test_product_codex_runner_rejects_any_extra_file(tmp_path,monkeypatch):
    import subprocess
    import ops.macos.shopping.dev_codex_website_jobs as jobs
    source=tmp_path/"source";source.mkdir()
    subprocess.run(["git","init","-q",str(source)],check=True)
    (source/"README.md").write_text("fixture")
    subprocess.run(["git","-C",str(source),"add","README.md"],check=True)
    subprocess.run(["git","-C",str(source),"-c","user.name=Test","-c","user.email=test@example.invalid","commit","-qm","fixture"],check=True)
    revision=subprocess.run(["git","-C",str(source),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    fake_cli=tmp_path/"codex-extra-fixture"
    fake_cli.write_text("""#!/usr/bin/env python3
import os,re,sys
text=sys.stdin.read();job=re.search(r'Product draft id: ([a-f0-9]{8})',text).group(1)
path='brands/agachichi/catalog/intake-drafts/'+job+'.json';os.makedirs(os.path.dirname(path),exist_ok=True)
open(path,'w').write('{}');open('README.md','a').write('unexpected')
""")
    fake_cli.chmod(0o700);monkeypatch.setattr(jobs,"CLI",fake_cli)
    worker=CodexWebsiteDraftWorker(SimpleNamespace(path=tmp_path/"dialogue.sqlite3",clock=time.time),
        revision=revision,source=source,data=tmp_path)
    assert worker._run("a1b2c3d4","PRODUCT_INTAKE::상품 등록: 셔츠")=="SCOPE_REJECTED"
