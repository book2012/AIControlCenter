from core.automation.executor import AutomationExecutor


def test_execute_status():
    executor = AutomationExecutor()

    result = executor.execute("/status")

    assert result["executed"] is True
    assert result["blocked"] is False
    assert "ONLINE" in result["result"]


def test_execute_blocks_unsafe_command():
    executor = AutomationExecutor()

    result = executor.execute("/backup run token")

    assert result["executed"] is False
    assert result["blocked"] is True
