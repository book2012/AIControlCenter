import yaml

from core.worker.local_runner import LocalRunner
from core.worker.ssh_runner import SSHRunner
from core.worker.ubuntu import UbuntuWorkerClient


class WorkerFactory:

    def __init__(self, config_path="config/workers.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def create(self, worker_name):

        cfg = self.config["workers"][worker_name]

        if cfg["mode"] == "local":
            runner = LocalRunner()

        else:
            runner = SSHRunner(
                host=cfg["host"],
                user=cfg.get("user"),
                port=cfg.get("port"),
                identity_file=cfg.get("identity_file"),
                timeout_seconds=cfg.get("timeout_seconds", 10),
                connect_timeout_seconds=cfg.get("connect_timeout_seconds", 5),
            )

        return UbuntuWorkerClient(
            scripts_path=cfg["scripts"],
            runner=runner,
        )
