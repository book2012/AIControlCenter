from fastapi import APIRouter

from core.datacenter.storage_registry import StorageRegistry

router = APIRouter()


@router.get("/storage")
def storage():
    return StorageRegistry().summary()
