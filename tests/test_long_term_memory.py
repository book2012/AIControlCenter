from core.memory.long_term import LongTermMemory


def test_long_term_memory_add_get():
    memory = LongTermMemory()

    item = memory.add("AIControlCenter is the Brain")

    loaded = memory.get(item["id"])

    assert loaded["content"] == "AIControlCenter is the Brain"


def test_long_term_memory_search():
    memory = LongTermMemory()

    memory.add("OpenAI provider is configured")
    memory.add("Telegram adapter is connected")

    results = memory.search("telegram")

    assert len(results) == 1
    assert results[0]["source"] == "manual"


def test_long_term_memory_status():
    memory = LongTermMemory()

    memory.add("hello")

    status = memory.status()

    assert status["ready"] is True
    assert status["items"] == 1
