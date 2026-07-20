from fastapi import APIRouter

from core.dashboard.api import DashboardAPI
from core.homepage.projection import apply_standalone_contract
from core.homepage.status import HomepageStatusService


router = APIRouter()

homepage = HomepageStatusService()
dashboard = DashboardAPI()


@router.get("/homepage/status")
def homepage_status():
    return apply_standalone_contract(
        homepage.status(),
        dashboard.status(["ubuntu-main"]),
    )
