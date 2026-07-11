from unittest.mock import patch

from core.worker.local_runner import LocalRunner
from core.worker.ubuntu import UbuntuWorkerClient


def test_storage_status_uses_approved_script() -> None:
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=LocalRunner(),
    )

    expected = {
        "overall_status": "HEALTHY",
        "database": {
            "integrity": "ok",
            "schema_version": "3",
        },
    }

    with patch(
        "core.worker.ubuntu.run_json_script",
        return_value=expected,
    ) as mocked:
        result = client.storage_status()

    assert result == expected
    mocked.assert_called_once_with(
        client.runner,
        "/opt/aihomedatacenter/scripts/"
        "commands/storage-agent-status.sh",
    )


def test_storage_db_status_uses_approved_script() -> None:
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=LocalRunner(),
    )

    expected = {
        "exists": True,
        "schema_version": "3",
        "files": 1_537_845,
        "scan_runs": 13,
    }

    with patch(
        "core.worker.ubuntu.run_json_script",
        return_value=expected,
    ) as mocked:
        result = client.storage_db_status()

    assert result == expected
    mocked.assert_called_once_with(
        client.runner,
        "/opt/aihomedatacenter/scripts/"
        "commands/storage-db-status.sh",
    )
