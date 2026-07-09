from fastapi import APIRouter

from core.dashboard.api import DashboardAPI

router = APIRouter()


@router.get("/dashboard")
def dashboard():
    return DashboardAPI().status()
