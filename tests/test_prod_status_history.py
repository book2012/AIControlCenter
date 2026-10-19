import sqlite3
from test_shop_aftersales_dev import fixture as aftersales_fixture, ORDER
from core.shopping.guest_aftersales import GuestAftersalesStore

def test_prod_status_history_records_cancellation_time_and_is_append_only(tmp_path):
    dev_store,_=aftersales_fixture(tmp_path,[1000.0])
    prod=GuestAftersalesStore(tmp_path/"prod-after.sqlite3",tmp_path/"prod-files",
        ledger=dev_store.ledger,checkout=dev_store.checkout,catalog=dev_store.catalog,
        clock=lambda:1234.5,
        stock_cancellation=lambda row,draft:{"outcome":"STOCK_CANCELLED","order_id":ORDER})
    result=prod.cancel_order(ORDER)
    assert result["state"]=="CANCELLED"
    events=prod.order_status_history(ORDER)
    assert [event["to_state"] for event in events]==["SENDING","CANCELLED"]
    assert all(event["changed_at"]==1234.5 for event in events)
    with sqlite3.connect(prod.path) as db:
        try:
            db.execute("UPDATE order_status_history SET to_state='NONE'")
            raise AssertionError("history update should be rejected")
        except sqlite3.IntegrityError:
            pass
        try:
            db.execute("DELETE FROM order_status_history")
            raise AssertionError("history deletion should be rejected")
        except sqlite3.IntegrityError:
            pass
