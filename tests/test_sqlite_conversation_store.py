from core.memory.sqlite_store import SQLiteConversationStore


def test_sqlite_conversation_store_create(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "test.db"))

    session = store.create_session()

    assert session["id"]
    assert session["messages"] == []


def test_sqlite_conversation_store_add_message(tmp_path):
    store = SQLiteConversationStore(str(tmp_path / "test.db"))

    session = store.create_session()
    store.add_message(session["id"], "user", "hello")

    loaded = store.get_session(session["id"])

    assert len(loaded["messages"]) == 1
    assert loaded["messages"][0]["role"] == "user"
