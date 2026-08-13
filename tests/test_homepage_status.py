from core.homepage.status import HomepageStatusService


def test_homepage_status():
    service = HomepageStatusService()

    data = service.status()

    assert "brain" in data
    assert "scheduler" in data
    assert "memory" in data
    assert "knowledge" in data
    assert data["scheduler"]["status"] in {"MISSING", "STALE", "ALIVE"}
    assert data["scheduler"]["status"] != "ONLINE"
