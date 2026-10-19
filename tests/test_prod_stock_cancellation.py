import json
import subprocess
import pytest

from ops.macos.shopping import prod_stock_cancellation as module

def test_cancel_provider_is_strictly_bound_to_production_and_test_is_stubbed(monkeypatch):
    calls=[]
    monkeypatch.setattr(module,"assert_production",lambda:calls.append("assert_prod"))
    monkeypatch.setattr(module,"DOCKER","/opt/homebrew/bin/docker",raising=False)
    class Result:
        returncode=0
        stdout=json.dumps({"outcome":"STOCK_CANCELLED","order_id":731})
    def fake_run(command,**kwargs):
        calls.append((command,kwargs))
        return Result()
    monkeypatch.setattr(module.subprocess,"run",fake_run)
    provider=module.ProductionStockCancellation(store=object())
    expected={"order_id":731,"tag":"order-tag","digest":"draft-digest","items":[]}
    result=provider.apply(expected)
    assert result["outcome"]=="STOCK_CANCELLED"
    command,kwargs=calls[1]
    assert calls[0]=="assert_prod"
    assert command[-2:]==["shopping-wordpress","php"]
    assert "aicc_shopping" in kwargs["input"]
    assert "aicc_order_dev" not in kwargs["input"]

def test_cancel_provider_refuses_wrong_receipt(monkeypatch):
    monkeypatch.setattr(module,"assert_production",lambda:None)
    monkeypatch.setattr(module,"DOCKER","docker",raising=False)
    class Result:
        returncode=0
        stdout=json.dumps({"outcome":"STOCK_CANCELLED","order_id":732})
    monkeypatch.setattr(module.subprocess,"run",lambda *a,**k:Result())
    with pytest.raises(RuntimeError,match="RECEIPT_INVALID"):
        module.ProductionStockCancellation(store=object()).apply(
            {"order_id":731,"tag":"order-tag","digest":"draft-digest","items":[]})
