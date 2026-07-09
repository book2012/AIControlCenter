from core.automation.policy import SafeExecutionPolicy


def test_policy_allows_status():
    result = SafeExecutionPolicy().check("/status")

    assert result["allowed"] is True


def test_policy_blocks_backup_run():
    result = SafeExecutionPolicy().check("/backup run token")

    assert result["allowed"] is False


def test_policy_blocks_unknown():
    result = SafeExecutionPolicy().check("/delete everything")

    assert result["allowed"] is False
