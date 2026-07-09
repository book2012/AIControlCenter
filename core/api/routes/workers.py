from fastapi import APIRouter

from core.dashboard.api import DashboardAPI

router = APIRouter()


@router.get("/workers")
def workers():
    return DashboardAPI().status(["ubuntu-main"])["workers"]


@router.get("/workers/{worker_id}")
def worker(worker_id: str):
    return DashboardAPI().status([worker_id])["workers"][worker_id]
