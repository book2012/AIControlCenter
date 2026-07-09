from fastapi import APIRouter
from pydantic import BaseModel

from core.task.executor import TaskExecutionManager


router = APIRouter()

manager = TaskExecutionManager()


class TaskRequest(BaseModel):
    worker: str
    command: str


@router.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            task.__dict__
            for task in manager.registry.tasks.values()
        ]
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    return manager.registry.get(task_id).__dict__


@router.post("/tasks")
def create_task(request: TaskRequest):
    task = manager.run(
        request.worker,
        request.command,
    )

    return task.__dict__
