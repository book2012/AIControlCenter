from pathlib import Path

from core.worker.factory import WorkerFactory
from core.worker.ssh_runner import SSHRunner


def test_worker_factory_propagates_ssh_timeouts(tmp_path: Path) -> None:
    config = tmp_path / "workers.yaml"
    config.write_text(
        "workers:\n"
        "  ubuntu-remote:\n"
        "    type: ubuntu\n"
        "    mode: ssh\n"
        "    host: 192.168.1.7\n"
        "    user: han\n"
        "    port: 22\n"
        "    scripts: /opt/aihomedatacenter/scripts\n"
        "    timeout_seconds: 12\n"
        "    connect_timeout_seconds: 4\n",
        encoding="utf-8",
    )

    worker = WorkerFactory(str(config)).create("ubuntu-remote")

    assert isinstance(worker.runner, SSHRunner)
    assert worker.runner.timeout_seconds == 12
    assert worker.runner.connect_timeout_seconds == 4
