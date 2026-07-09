from core.homepage.status import HomepageStatusService


def test_homepage_status():
    service = HomepageStatusService()

    data = service.status()

    assert "brain" in data
    assert "scheduler" in data
    assert "memory" in data
    assert "knowledge" in data
