from fastapi import APIRouter, HTTPException
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
            task.to_dict()
            for task in manager.registry.tasks.values()
        ]
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    try:
        return manager.registry.get(task_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@router.post("/tasks")
def create_task(request: TaskRequest):
    task = manager.run(
        request.worker,
        request.command,
    )

    return task.to_dict()
