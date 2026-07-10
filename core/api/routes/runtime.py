from fastapi import APIRouter

from core.runtime.service_health import ServiceHealth


router = APIRouter()
service_health = ServiceHealth()


@router.get("/runtime/health")
def runtime_health():
    return service_health.status()
