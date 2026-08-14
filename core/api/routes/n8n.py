"""GET-only AIControlCenter projection of the n8n capability."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("/n8n")
def n8n_status(request: Request) -> dict[str, object]:
    return request.app.state.n8n_status_service.status()
