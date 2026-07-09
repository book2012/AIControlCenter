from datetime import datetime
from uuid import uuid4


class LongTermMemory:
    def __init__(self):
        self.items = {}

    def add(self, content: str, source: str = "manual", metadata: dict | None = None):
        item_id = str(uuid4())

        item = {
            "id": item_id,
            "content": content,
            "source": source,
            "metadata": metadata or {},
            "created": datetime.utcnow().isoformat(),
        }

        self.items[item_id] = item
        return item

    def get(self, item_id: str):
        return self.items.get(item_id)

    def list(self):
        return list(self.items.values())

    def search(self, query: str):
        query_lower = query.lower()

        return [
            item
            for item in self.items.values()
            if query_lower in item["content"].lower()
        ]

    def status(self):
        return {
            "type": "long_term",
            "items": len(self.items),
            "ready": True,
        }
