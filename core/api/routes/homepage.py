from fastapi import APIRouter

from core.homepage.status import HomepageStatusService


router = APIRouter()

homepage = HomepageStatusService()


@router.get("/homepage/status")
def homepage_status():
    return homepage.status()
