from core.logs.service import LogsService


def test_logs_service_missing_root(tmp_path):
    service = LogsService(str(tmp_path / "missing"))

    result = service.recent()

    assert result["exists"] is False
    assert result["logs"] == []


def test_logs_service_recent(tmp_path):
    root = tmp_path / "logs"
    root.mkdir()

    (root / "a.log").write_text("hello")

    service = LogsService(str(root))

    result = service.recent()

    assert result["exists"] is True
    assert len(result["logs"]) == 1
    assert result["logs"][0]["name"] == "a.log"


def test_logs_service_format_text(tmp_path):
    root = tmp_path / "logs"
    root.mkdir()

    (root / "a.log").write_text("hello")

    service = LogsService(str(root))

    text = service.format_text()

    assert "Recent Logs" in text
    assert "a.log" in text
