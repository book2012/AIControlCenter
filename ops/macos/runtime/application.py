"""macOS Production composition root for the canonical API."""

from core.api.app import create_app
from core.runtime.service_health import ServiceHealth
from integrations.openclaw import build_openclaw_status_service
from ops.macos.launchd import application_scheduler_logs


service_health = ServiceHealth(
    scheduler_log_inspector=application_scheduler_logs.inspect_contract,
)
app = create_app(
    service_health=service_health,
    openclaw_status_service=build_openclaw_status_service(),
)
