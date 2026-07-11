from fastapi import APIRouter

from core.datacenter.snapshot import DatacenterSnapshotService
from core.worker.factory import WorkerFactory

router = APIRouter()


@router.get("/datacenter/status")
def datacenter_status():
    worker = WorkerFactory().create("ubuntu-main")
    return DatacenterSnapshotService(worker).status()
