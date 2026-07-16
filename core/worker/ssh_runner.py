import subprocess

from core.worker.runner import Runner


class SSHRunner(Runner):

    def __init__(
        self,
        host,
        user=None,
        port=None,
        identity_file=None,
        timeout_seconds=10,
        connect_timeout_seconds=5,
    ):
        self.host = host
        self.user = user
        self.port = port
        self.identity_file = identity_file
        self.timeout_seconds = timeout_seconds
        self.connect_timeout_seconds = connect_timeout_seconds

    def run(self, command):

        if isinstance(command, list):
            command = " ".join(command)

        target = self.host

        if self.user:
            target = f"{self.user}@{self.host}"

        ssh = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={self.connect_timeout_seconds}",
        ]

        if self.port:
            ssh.extend(["-p", str(self.port)])

        if self.identity_file:
            ssh.extend(
                [
                    "-i",
                    self.identity_file,
                    "-o",
                    "IdentitiesOnly=yes",
                ]
            )

        ssh.extend([target, command])
        try:
            result = subprocess.run(
                ssh,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("ssh_command_timeout") from exc

        return result.stdout.strip()
