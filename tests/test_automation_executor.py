from core.automation.executor import AutomationExecutor


def test_execute_status():
    executor = AutomationExecutor()

    result = executor.execute("/status")

    assert result["executed"] is True
    assert "ONLINE" in result["result"]


def test_execute_doctor():
    executor = AutomationExecutor()

    result = executor.execute("/doctor")

    assert result["executed"] is True
