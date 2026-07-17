import os

import yaml

from core.worker.local_runner import LocalRunner
from core.worker.ssh_runner import SSHRunner
from core.worker.ubuntu import UbuntuWorkerClient


class WorkerFactory:

    def __init__(self, config_path: str | None = None):
        selected_path = config_path or os.environ.get(
            "AICONTROLCENTER_WORKERS_CONFIG",
            "config/workers.yaml",
        )
        with open(selected_path, "r", encoding="utf-8") as file:
            raw_config = file.read()

        expanded_config = os.path.expandvars(raw_config)
        if "${" in expanded_config:
            raise ValueError("unresolved_worker_config_environment")

        self.config = yaml.safe_load(expanded_config)

    def create(self, worker_name):

        cfg = self.config["workers"][worker_name]

        if cfg["mode"] == "local":
            runner = LocalRunner()

        else:
            runner = SSHRunner(
                host=cfg["host"],
                user=cfg.get("user"),
                port=(
                    int(cfg["port"])
                    if cfg.get("port") is not None
                    else None
                ),
                identity_file=cfg.get("identity_file"),
                timeout_seconds=cfg.get("timeout_seconds", 10),
                connect_timeout_seconds=cfg.get("connect_timeout_seconds", 5),
            )

        return UbuntuWorkerClient(
            scripts_path=cfg["scripts"],
            runner=runner,
        )
