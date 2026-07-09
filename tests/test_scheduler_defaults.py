from core.scheduler.defaults import create_default_jobs


def test_create_default_jobs():
    jobs = create_default_jobs().list()
    names = [job["name"] for job in jobs]

    assert "heartbeat" in names
    assert "doctor" in names
    assert "provider-check" in names
    assert "backup-verify" in names
