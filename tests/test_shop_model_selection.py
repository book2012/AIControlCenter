import json

import pytest

from core.shopping.operator_intent import LocalOperatorJudge
from ops.macos.shopping.dev_local_inquiry import LocalInquiryJudge


class _Response:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self.content = b"{}"
        self._payload = payload or {"done": True, "response": json.dumps({"action": "UNKNOWN"})}

    def json(self):
        return self._payload


class _Session:
    def __init__(self):
        self.models = []
        self.trust_env = True

    def post(self, _url, *, json, **_kwargs):
        self.models.append(json["model"])
        if len(self.models) == 1:
            return _Response(status=503)
        return _Response()


def test_operator_8b_uses_4b_fallback_after_primary_failure():
    session = _Session()
    judge = LocalOperatorJudge(model="qwen3:8b", fallback_model="qwen3:4b", session=session)
    assert judge("무엇을 해야 해?", {"products": []}) == {"action": "UNKNOWN"}
    assert session.models == ["qwen3:8b", "qwen3:4b"]


def test_inquiry_accepts_supported_dev_models_only():
    assert LocalInquiryJudge(model="qwen3:8b").model == "qwen3:8b"
    assert LocalInquiryJudge(model="qwen3:4b").model == "qwen3:4b"
    with pytest.raises(ValueError, match="EXPLICIT_LOCAL_MODEL_REQUIRED"):
        LocalInquiryJudge(model="qwen3:14b")


def test_customer_inquiry_can_use_fast_model_while_operator_stays_on_primary():
    from pathlib import Path
    source = Path("ops/macos/shopping/dev_order_runtime.py").read_text()
    assert 'conversation_cfg.get("inquiry_model",conversation_cfg.get("model","qwen3:4b"))' in source
