from fastapi import FastAPI

from core.config.loader import ConfigLoader

from core.api.routes import agents, automation, backup, brain, conversations, dashboard, datacenter, health, homepage, knowledge, memory, n8n, notifications, openclaw, planner, providers, runtime, scheduler, shopping, storage, tasks, workers
from core.api.routes.ollama import router as ollama_router
from core.api.routes.model_governance import router as model_governance_router
from core.api.routes.governance_audit import router as governance_audit_router
from core.api.routes.deployment import router as deployment_router
from core.runtime.service_health import ServiceHealth
from core.capabilities import CapabilityObservation, CapabilityStatus
from core.capabilities.service import CapabilityStatusService
from core.shopping.runtime_composition import build_shopping_runtime
from core.notifications import NotificationPlatform


class _UnavailableOpenClawObserver:
    """Platform-neutral fallback that performs no integration discovery."""

    def observe(self) -> CapabilityObservation:
        return CapabilityObservation(
            provider="openclaw",
            service_id="openclaw",
            status=CapabilityStatus.UNAVAILABLE,
            available=False,
            healthy=False,
            ready=False,
            capabilities=(),
            configuration={"status": "UNKNOWN"},
            runtime={"kind": "UNKNOWN"},
            evidence=(),
            error={"error_type": "ObserverNotConfigured"},
        )


class _UnavailableN8nObserver:
    """Platform-neutral fallback that performs no integration discovery."""

    def observe(self) -> CapabilityObservation:
        return CapabilityObservation(
            provider="n8n", service_id="n8n",
            status=CapabilityStatus.UNAVAILABLE,
            available=False, healthy=False, ready=False, capabilities=(),
            configuration={"status": "UNKNOWN"},
            runtime={"kind": "UNKNOWN", "transport": "UNKNOWN"},
            evidence=(), error={"error_type": "ObserverNotConfigured"},
        )


def create_app(
    service_health: ServiceHealth | None = None,
    openclaw_status_service: CapabilityStatusService | None = None,
    n8n_status_service: CapabilityStatusService | None = None,
    notification_platform: NotificationPlatform | None = None,
) -> FastAPI:
    ConfigLoader().load()
    app = FastAPI(
        title="AIControlCenter",
        description="AI Home Infrastructure Control Plane",
        version="0.1.0",
    )
    app.state.service_health = service_health or ServiceHealth()
    app.state.openclaw_status_service = openclaw_status_service or CapabilityStatusService(
        _UnavailableOpenClawObserver()
    )
    app.state.n8n_status_service = n8n_status_service or CapabilityStatusService(
        _UnavailableN8nObserver()
    )
    app.state.notification_platform = notification_platform or NotificationPlatform()
    app.state.shopping_runtime = build_shopping_runtime()

    app.include_router(health.router)
    app.include_router(homepage.router)
    app.include_router(runtime.router)
    app.include_router(openclaw.router)
    app.include_router(n8n.router)
    app.include_router(notifications.router)
    app.include_router(memory.router)
    app.include_router(knowledge.router)
    app.include_router(scheduler.router)
    app.include_router(agents.router)
    app.include_router(automation.router)
    app.include_router(conversations.router)
    app.include_router(brain.router)
    app.include_router(dashboard.router)
    app.include_router(shopping.router)
    app.include_router(storage.router)
    app.include_router(backup.router)
    app.include_router(planner.router)
    app.include_router(providers.router)
    app.include_router(tasks.router)
    app.include_router(workers.router)
    app.include_router(datacenter.router)

    app.include_router(ollama_router)
    app.include_router(model_governance_router)
    app.include_router(governance_audit_router)
    app.include_router(deployment_router)
    return app


app = create_app()
