from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/runtime/health")
def runtime_health(request: Request):
    return request.app.state.service_health.status()
