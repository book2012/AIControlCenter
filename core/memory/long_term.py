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
        words = [
            word.lower()
            for word in query.replace("/", " ").split()
            if word.strip()
        ]

        results = []

        for item in self.items.values():
            content = item["content"].lower()

            if any(word in content for word in words):
                results.append(item)

        return results

    def status(self):
        return {
            "type": "long_term",
            "items": len(self.items),
            "ready": True,
        }
