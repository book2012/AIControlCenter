"""macOS Production composition root for the canonical API."""

from core.api.app import create_app
from core.runtime.service_health import ServiceHealth
from integrations.openclaw import build_openclaw_status_service
from integrations.n8n import build_n8n_status_service
from integrations.notifications import build_telegram_notification_adapter
from integrations.woocommerce import build_woocommerce_status_service
from core.notifications import NotificationPlatform, NotificationProviderRegistry
from ops.macos.launchd import application_scheduler_logs


service_health = ServiceHealth(
    scheduler_log_inspector=application_scheduler_logs.inspect_contract,
)
app = create_app(
    service_health=service_health,
    openclaw_status_service=build_openclaw_status_service(),
    n8n_status_service=build_n8n_status_service(),
    notification_platform=NotificationPlatform(NotificationProviderRegistry((
        build_telegram_notification_adapter(),
    ))),
    woocommerce_status_service=build_woocommerce_status_service(),
)
