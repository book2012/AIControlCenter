from datetime import datetime, timedelta, timezone

from core.scheduler.heartbeat import HeartbeatStore, classify_heartbeat


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


def test_heartbeat_classification_missing():
    now = datetime.now(timezone.utc)

    assert classify_heartbeat(None, now=now)["status"] == "MISSING"


def test_future_alive_heartbeat_fails_closed():
    now = datetime.now(timezone.utc)

    result = classify_heartbeat(
        {"status": "ALIVE", "created": (now + timedelta(seconds=1)).isoformat()},
        now=now,
    )

    assert result["status"] == "STALE"
    assert result["fresh"] is False


def test_recent_error_heartbeat_fails_closed():
    now = datetime.now(timezone.utc)

    result = classify_heartbeat(
        {"status": "ERROR", "created": (now - timedelta(seconds=30)).isoformat()},
        now=now,
    )

    assert result["status"] == "STALE"
    assert result["fresh"] is False


def test_recent_dead_heartbeat_fails_closed():
    now = datetime.now(timezone.utc)

    result = classify_heartbeat(
        {"status": "DEAD", "created": (now - timedelta(seconds=30)).isoformat()},
        now=now,
    )

    assert result["status"] == "STALE"
    assert result["fresh"] is False


def test_valid_recent_alive_heartbeat_remains_alive():
    now = datetime.now(timezone.utc)

    result = classify_heartbeat(
        {"status": "ALIVE", "created": (now - timedelta(seconds=30)).isoformat()},
        now=now,
    )

    assert result["status"] == "ALIVE"
    assert result["fresh"] is True
    assert result["freshness_seconds"] == 90


def test_malformed_created_value_fails_closed():
    result = classify_heartbeat({"status": "ALIVE", "created": "not-a-date"})

    assert result["status"] == "STALE"
    assert result["fresh"] is False
    assert result["age_seconds"] is None
