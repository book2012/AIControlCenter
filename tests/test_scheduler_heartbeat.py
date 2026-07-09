from core.scheduler.heartbeat import HeartbeatStore


def test_heartbeat_store_beat(tmp_path):
    store = HeartbeatStore(str(tmp_path / "scheduler.db"))

    result = store.beat()

    assert result["status"] == "ALIVE"
    assert result["created"]


def test_heartbeat_store_latest(tmp_path):
    store = HeartbeatStore(str(tmp_path / "scheduler.db"))

    store.beat()
    latest = store.latest()

    assert latest["status"] == "ALIVE"
