from fastapi import FastAPI

from core.config.loader import ConfigLoader

from core.api.routes import agents, backup, brain, conversations, dashboard, health, knowledge, memory, notifications, providers, scheduler, storage, tasks, workers


def create_app() -> FastAPI:
    ConfigLoader().load()
    app = FastAPI(
        title="AIControlCenter",
        description="AI Home Infrastructure Control Plane",
        version="0.1.0",
    )

    app.include_router(health.router)
    app.include_router(notifications.router)
    app.include_router(memory.router)
    app.include_router(knowledge.router)
    app.include_router(scheduler.router)
    app.include_router(notifications.router)
    app.include_router(memory.router)
    app.include_router(knowledge.router)
    app.include_router(scheduler.router)
    app.include_router(agents.router)
    app.include_router(conversations.router)
    app.include_router(brain.router)
    app.include_router(dashboard.router)
    app.include_router(storage.router)
    app.include_router(backup.router)
    app.include_router(providers.router)
    app.include_router(tasks.router)
    app.include_router(workers.router)

    return app


app = create_app()
