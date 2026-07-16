import subprocess
from unittest.mock import patch

import pytest

from core.worker.ssh_runner import SSHRunner


def test_create_runner() -> None:
    runner = SSHRunner(
        host="localhost",
        user="han",
    )

    assert runner.host == "localhost"
    assert runner.user == "han"


def test_ssh_runner_uses_bounded_timeouts() -> None:
    runner = SSHRunner(
        host="192.168.1.7",
        user="han",
        port=22,
        timeout_seconds=10,
        connect_timeout_seconds=5,
    )

    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"status":"ONLINE"}',
        stderr="",
    )

    with patch("core.worker.ssh_runner.subprocess.run", return_value=completed) as run:
        output = runner.run(["bash", "/opt/worker-health.sh"])

    command = run.call_args.args[0]
    assert "BatchMode=yes" in command
    assert "ConnectTimeout=5" in command
    assert run.call_args.kwargs["timeout"] == 10
    assert output == '{"status":"ONLINE"}'


def test_ssh_runner_normalizes_timeout() -> None:
    runner = SSHRunner(
        host="192.168.1.7",
        timeout_seconds=3,
    )

    expired = subprocess.TimeoutExpired(
        cmd=["ssh"],
        timeout=3,
    )

    with patch("core.worker.ssh_runner.subprocess.run", side_effect=expired):
        with pytest.raises(TimeoutError, match="ssh_command_timeout"):
            runner.run(["bash", "/opt/worker-health.sh"])
