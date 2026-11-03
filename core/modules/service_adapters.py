"""Independent service adapters. No private note retrieval or assistant execution."""
from fastapi import FastAPI

CREATIVE_NOTES_URL = "https://bok-creative-notes.kyouhan.chatgpt.site"
CREATIVE_NOTES_PROJECT = "appgprj_6ad80723fd208191b3617a9dac8ca392"


def create_creative_notes_adapter():
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    @app.get("/health")
    def health():
        return {"service": "creative-notes", "mode": "external_service_reference",
                "upstream_health": "NOT_OBSERVED", "authenticated_api": "NOT_CONNECTED"}
    @app.get("/connection")
    def connection():
        return {"service": "creative-notes", "website": CREATIVE_NOTES_URL,
                "project_id": CREATIVE_NOTES_PROJECT, "data_owner": "Sites D1/R2",
                "authentication": "existing per-account Sites authentication",
                "detach_effect": "disconnect platform adapter; retain hosted site and data",
                "private_notes_access": False}
    return app


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
