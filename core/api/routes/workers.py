from fastapi import APIRouter

from core.dashboard.api import DashboardAPI

router = APIRouter()


@router.get("/workers")
def workers():
    return DashboardAPI().status(
        ["ubuntu-main"],
        include_datacenter=False,
    )["workers"]


@router.get("/workers/{worker_id}")
def worker(worker_id: str):
    return DashboardAPI().status(
        [worker_id],
        include_datacenter=False,
    )["workers"][worker_id]
