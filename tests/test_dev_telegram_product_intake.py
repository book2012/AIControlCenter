"""DEV Telegram product intake queues only Codex review, never commerce writes."""
import sqlite3
import time
from types import SimpleNamespace

from test_shop_operator_conversation import env, ACTOR, OTHER
from ops.macos.shopping.dev_codex_website_jobs import CodexWebsiteDraftWorker


def _job(engine):
    with sqlite3.connect(engine.path) as db:
        return db.execute("SELECT id,actor,request,state FROM website_jobs").fetchone()


def test_menu_guidance_and_one_product_draft_per_update(env):
    engine = env.engine
    assert "상품 등록:" in engine.handle("상품 등록", 1, ACTOR)
    text = "상품 등록: 린넨 셔츠, 39,000원, 재고 확인 필요"
    reply = engine.handle(text, 2, ACTOR)
    job, actor, request, state = _job(engine)
    assert job in reply and actor == ACTOR
    assert request == "PRODUCT_INTAKE::린넨 셔츠, 39,000원, 재고 확인 필요" and state == "WAITING_CODEX"
    assert engine.handle(text, 2, ACTOR) == reply
    assert "찾지 못" in engine.handle("상품초안 #" + job, 3, OTHER)
    assert "Codex 대기" in engine.handle("상품초안 #" + job, 4, ACTOR)
    assert job in engine.handle("상품초안 목록", 5, ACTOR)
    assert not env.calls and not env.contexts


def test_codex_completion_notifies_operator_without_registering(env, tmp_path):
    engine = env.engine
    engine.handle("상품 등록: 코튼 셔츠, 39,000원", 1, ACTOR)
    job = _job(engine)[0]
    calls = []
    worker = CodexWebsiteDraftWorker(engine, revision="a" * 40,
        source=tmp_path, data=tmp_path,
        runner=lambda name, request: (calls.append((name, request)) or "PRODUCT_REVIEW_REQUIRED"))
    worker.start_one()
    for _ in range(100):
        if _job(engine)[3] != "CODEX_RUNNING":
            break
        time.sleep(.01)
    assert _job(engine)[3] == "PRODUCT_REVIEW_REQUIRED"
    assert calls == [(job, "PRODUCT_INTAKE::코튼 셔츠, 39,000원")]
    notices = []
    assert engine.notify_one(SimpleNamespace(send_message=lambda body: notices.append(body))) == "SENT"
    assert job in notices[0] and "상품정보·사진 검토 전에는 등록되지" in notices[0]
    assert "검토 대기" in engine.handle("상품초안 #" + job, 2, ACTOR)
    assert not env.calls
