from unittest.mock import patch

from core.worker.local_runner import LocalRunner
from core.worker.ubuntu import UbuntuWorkerClient


def test_backup_status_uses_approved_script() -> None:
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=LocalRunner(),
    )

    expected = {
        "overall_status": "HEALTHY",
        "backup": {
            "root": "/mnt/storage/Backup",
            "exists": True,
            "readable": True,
        },
        "filesystem": {
            "used_percent": 71.72,
            "status": "OK",
        },
        "safety": {
            "read_only": True,
            "automatic_deletion": False,
        },
    }

    with patch(
        "core.worker.ubuntu.run_json_script",
        return_value=expected,
    ) as mocked:
        result = client.backup_status()

    assert result == expected
    mocked.assert_called_once_with(
        client.runner,
        "/opt/aihomedatacenter/scripts/"
        "commands/backup-status-json.sh",
    )
