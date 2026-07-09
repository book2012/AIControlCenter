from core.worker_status.service import WorkerStatusService


def test_worker_status_format_text():
    service = WorkerStatusService()

    text = service.format_text(["missing-worker"])

    assert "Workers" in text
    assert "missing-worker" in text
    assert "OPTIONAL_UNAVAILABLE" in text
