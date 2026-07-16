import pytest

from core.worker.ubuntu import UbuntuWorkerClient


class FakeRunner:
    def __init__(self, output: str) -> None:
        self.output = output
        self.commands: list[list[str]] = []

    def run(self, command: list[str]) -> str:
        self.commands.append(command)
        return self.output


def test_ubuntu_worker_health_status_uses_json_contract() -> None:
    runner = FakeRunner(
        '{"schema_version":1,"worker_id":"ubuntu-main",'
        '"role":"stateless-infrastructure-worker",'
        '"health":"ONLINE","available":true}'
    )
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=runner,
    )

    result = client.health_status()

    assert result["schema_version"] == 1
    assert result["worker_id"] == "ubuntu-main"
    assert result["health"] == "ONLINE"
    assert result["available"] is True
    assert runner.commands == [[
        "bash",
        "/opt/aihomedatacenter/scripts/commands/worker-health-json.sh",
    ]]


def test_ubuntu_worker_health_status_rejects_invalid_json() -> None:
    client = UbuntuWorkerClient(
        scripts_path="/opt/aihomedatacenter/scripts",
        runner=FakeRunner("not-json"),
    )

    with pytest.raises(ValueError, match="invalid_worker_health_json"):
        client.health_status()
