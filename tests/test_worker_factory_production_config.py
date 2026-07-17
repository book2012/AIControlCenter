from pathlib import Path

from core.worker.factory import WorkerFactory
from core.worker.ssh_runner import SSHRunner


def test_worker_factory_uses_environment_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = tmp_path / "workers.yaml"
    config.write_text(
        "workers:\n"
        "  ubuntu-main:\n"
        "    type: ubuntu\n"
        "    mode: ssh\n"
        "    host: ${DATACENTER_HOST}\n"
        "    user: ${DATACENTER_SSH_USER}\n"
        "    port: ${DATACENTER_SSH_PORT}\n"
        "    scripts: /opt/aihomedatacenter/scripts\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AICONTROLCENTER_WORKERS_CONFIG", str(config))
    monkeypatch.setenv("DATACENTER_HOST", "192.168.1.7")
    monkeypatch.setenv("DATACENTER_SSH_USER", "han")
    monkeypatch.setenv("DATACENTER_SSH_PORT", "22")

    worker = WorkerFactory().create("ubuntu-main")

    assert isinstance(worker.runner, SSHRunner)
    assert worker.runner.host == "192.168.1.7"
    assert worker.runner.user == "han"
    assert worker.runner.port == 22


def test_worker_factory_rejects_unexpanded_environment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = tmp_path / "workers.yaml"
    config.write_text(
        "workers:\n"
        "  ubuntu-main:\n"
        "    mode: ssh\n"
        "    host: ${MISSING_HOST}\n"
        "    user: han\n"
        "    port: 22\n"
        "    scripts: /opt/scripts\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AICONTROLCENTER_WORKERS_CONFIG", str(config))

    try:
        WorkerFactory()
    except ValueError as error:
        assert str(error) == "unresolved_worker_config_environment"
    else:
        raise AssertionError("ValueError was not raised")
