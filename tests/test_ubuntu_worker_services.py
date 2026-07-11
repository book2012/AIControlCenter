from unittest.mock import patch

from core.worker.local_runner import LocalRunner
from core.worker.ubuntu import UbuntuWorkerClient


def test_services_status_uses_approved_script() -> None:
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=LocalRunner(),
    )

    expected = {
        "docker_available": True,
        "overall_status": "HEALTHY",
        "services": {
            "immich": {
                "status": "HEALTHY",
                "containers_total": 4,
                "containers_running": 4,
            },
            "nextcloud": {
                "status": "HEALTHY",
                "containers_total": 3,
                "containers_running": 3,
            },
        },
        "safety": {
            "read_only": True,
        },
    }

    with patch(
        "core.worker.ubuntu.run_json_script",
        return_value=expected,
    ) as mocked:
        result = client.services_status()

    assert result == expected
    mocked.assert_called_once_with(
        client.runner,
        "/opt/aihomedatacenter/scripts/"
        "commands/services-status-json.sh",
    )
