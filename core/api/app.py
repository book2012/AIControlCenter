from fastapi import FastAPI

from core.api.routes import backup, brain, dashboard, health, storage, workers


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIControlCenter",
        description="AI Home Infrastructure Control Plane",
        version="0.1.0",
    )

    app.include_router(health.router)
    app.include_router(brain.router)
    app.include_router(dashboard.router)
    app.include_router(storage.router)
    app.include_router(backup.router)
    app.include_router(workers.router)

    return app


app = create_app()
