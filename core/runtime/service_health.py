import subprocess
from collections.abc import Callable

from core.scheduler.heartbeat import HeartbeatStore, classify_heartbeat
from core.runtime.service_topology import (
    ServiceTopology,
    TopologyConfigurationError,
)


def unavailable_scheduler_log_inspector() -> dict:
    return {
        "scheduler_log_contract_ready": False,
        "inspection_error": {"error_type": "AdapterNotConfigured"},
    }


class ServiceHealth:
    def __init__(
        self,
        heartbeat: HeartbeatStore | None = None,
        heartbeat_timeout_seconds: int = 90,
        topology: ServiceTopology | None = None,
        launchd_inspector: Callable[[str], str] | None = None,
        scheduler_log_inspector: Callable[[], dict] | None = None,
    ):
        self.heartbeat = heartbeat or HeartbeatStore()
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.topology = topology or ServiceTopology()
        self.launchd_inspector = launchd_inspector or self.launchd_status
        self.scheduler_log_inspector = (
            scheduler_log_inspector or unavailable_scheduler_log_inspector
        )

    def launchd_status(self, label: str) -> str:
        try:
            result = subprocess.run(
                ["/bin/launchctl", "print", f"system/{label}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                return "STOPPED"
            return "RUNNING" if "state = running" in result.stdout else "STOPPED"
        except (OSError, subprocess.SubprocessError):
            return "UNAVAILABLE"

    def heartbeat_status(self):
        return classify_heartbeat(
            self.heartbeat.latest(),
            self.heartbeat_timeout_seconds,
        )

    def status(self):
        heartbeat = self.heartbeat_status()
        try:
            scheduler_logs = self.scheduler_log_inspector()
            scheduler_logs_ready = (
                scheduler_logs.get("scheduler_log_contract_ready") is True
            )
        except Exception as exc:
            scheduler_logs = {
                "scheduler_log_contract_ready": False,
                "inspection_error": {"error_type": type(exc).__name__},
            }
            scheduler_logs_ready = False
        try:
            topology_services = self.topology.runtime_services()
        except TopologyConfigurationError:
            return {
                "healthy": False,
                "services": {},
                "scheduler_heartbeat": heartbeat,
                "scheduler_log_readiness": scheduler_logs,
                "topology": {"status": "INVALID"},
            }

        services = {}
        for service in topology_services:
            if service.lifecycle == "launchd":
                state = self.launchd_inspector(service.launchd_label or "")
            elif service.deployment_status == "NOT_DEPLOYED":
                state = "NOT_DEPLOYED"
            else:
                state = "UNAVAILABLE"
            services[service.logical_id] = {
                "service_id": service.service_id,
                "required": service.required,
                "lifecycle": service.lifecycle,
                "status": state,
                **(
                    {"launchd_label": service.launchd_label}
                    if service.launchd_label is not None
                    else {}
                ),
            }

        healthy = all(
            not item["required"] or item["status"] == "RUNNING"
            for item in services.values()
        )
        scheduler = services.get("scheduler")
        if (
            scheduler and scheduler["required"]
            and (not heartbeat["fresh"] or not scheduler_logs_ready)
        ):
            healthy = False

        return {
            "healthy": healthy,
            "services": services,
            "scheduler_heartbeat": heartbeat,
            "scheduler_log_readiness": scheduler_logs,
            "topology": {"status": "VALID"},
        }

    def format_text(self):
        data = self.status()

        lines = [
            "🛠 Service Health",
            "",
        ]

        for name, item in data["services"].items():
            marker = "✅" if item["status"] == "RUNNING" else "❌"
            lines.append(f"{marker} {name}: {item['status']}")

        heartbeat = data["scheduler_heartbeat"]
        marker = "✅" if heartbeat["fresh"] else "❌"
        lines.extend([
            "",
            f"{marker} heartbeat: {heartbeat['status']}",
            "",
            f"Overall: {'HEALTHY' if data['healthy'] else 'WARNING'}",
        ])

        return "\n".join(lines)
