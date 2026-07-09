from fastapi import APIRouter

from core.datacenter.backup_registry import BackupRegistry

router = APIRouter()


@router.get("/backup")
def backup():
    return BackupRegistry().summary()
