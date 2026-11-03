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
