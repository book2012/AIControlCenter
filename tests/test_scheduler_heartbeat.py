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


def test_latest_does_not_create_database_or_parent(tmp_path):
    db_path = tmp_path / "missing" / "scheduler.db"
    store = HeartbeatStore(str(db_path))

    assert store.latest() is None
    assert not db_path.exists()
    assert not db_path.parent.exists()


def test_latest_does_not_migrate_database(tmp_path):
    db_path = tmp_path / "scheduler.db"
    db_path.write_bytes(b"not a sqlite database")
    before = db_path.stat().st_mtime_ns

    assert HeartbeatStore(str(db_path)).latest() is None
    assert db_path.stat().st_mtime_ns == before
