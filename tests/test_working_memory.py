from core.memory.working import WorkingMemory


def test_working_memory_set_get():
    memory = WorkingMemory()

    memory.set("current_focus", "scheduler")

    item = memory.get("current_focus")

    assert item["value"] == "scheduler"


def test_working_memory_delete():
    memory = WorkingMemory()

    memory.set("a", "b")
    deleted = memory.delete("a")

    assert deleted["value"] == "b"
    assert memory.get("a") is None


def test_working_memory_status():
    memory = WorkingMemory()

    memory.set("a", "b")

    status = memory.status()

    assert status["ready"] is True
    assert status["items"] == 1
