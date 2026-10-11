"""Website automation drafts are isolated, bounded, reviewed and claimed once."""
import sqlite3
import time
from pathlib import Path
from test_shop_operator_conversation import env,ACTOR
from ops.macos.shopping.dev_codex_website_jobs import CodexWebsiteDraftWorker,draft_arguments,draft_prompt

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
