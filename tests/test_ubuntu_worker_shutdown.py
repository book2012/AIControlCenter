from unittest.mock import patch

from core.worker.local_runner import LocalRunner
from core.worker.ubuntu import UbuntuWorkerClient


def test_shutdown_plan_uses_guarded_command() -> None:
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=LocalRunner(),
    )

    expected = {
        "mode": "dry-run",
        "approved": False,
        "executed": False,
        "blocking_reasons": ["running_containers"],
    }

    with patch(
        "core.worker.ubuntu.run_json_script",
        return_value=expected,
    ) as mocked:
        result = client.shutdown_plan()

    assert result == expected
    assert result["executed"] is False

    mocked.assert_called_once_with(
        client.runner,
        "/opt/aihomedatacenter/scripts/"
        "commands/safe-shutdown-json.sh",
    )
