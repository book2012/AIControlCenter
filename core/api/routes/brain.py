from fastapi import APIRouter

from core.brain.status import BrainStatus

router = APIRouter()


@router.get("/brain")
def brain():
    return BrainStatus().status()
