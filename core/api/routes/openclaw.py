"""GET-only AIControlCenter projection of the OpenClaw capability."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("/openclaw")
def openclaw_status(request: Request) -> dict[str, object]:
    return request.app.state.openclaw_status_service.status()
