from core.memory.conversation import ConversationMemory


def test_conversation_memory_create():
    memory = ConversationMemory()

    session = memory.create()

    assert session.id
    assert session.messages == []


def test_conversation_memory_add_message():
    memory = ConversationMemory()

    session = memory.create()
    memory.add_message(session.id, "user", "hello")

    data = session.to_dict()

    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"
