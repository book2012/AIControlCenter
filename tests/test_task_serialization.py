from core.task.registry import TaskRegistry


def test_task_to_dict_datetime_serialization():
    registry = TaskRegistry()

    task = registry.start("ubuntu-main", "status")
    finished = registry.finish(task.id, result={"ok": True})

    data = finished.to_dict()

    assert isinstance(data["started"], str)
    assert isinstance(data["finished"], str)
    assert data["result"]["ok"] is True
