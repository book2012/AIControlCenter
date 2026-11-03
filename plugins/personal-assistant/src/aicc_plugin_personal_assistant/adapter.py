from fastapi import FastAPI

def create_personal_assistant_adapter(status_service=None):
    # Provider implementation is injected by outer composition; core never imports it.
    from core.capabilities.service import CapabilityStatusService
    from core.capabilities import UnavailableCapabilityObserver
    status = status_service or CapabilityStatusService(UnavailableCapabilityObserver("openclaw", "openclaw"))
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    @app.get("/health")
    def health():
        return status.status()
    @app.get("/connection")
    def connection():
        return {"service": "personal-assistant", "provider": "openclaw",
                "authenticated_api": "NOT_CONNECTED", "execution_enabled": False,
                "detach_effect": "disconnect platform adapter; preserve independent runtime"}
    return app
