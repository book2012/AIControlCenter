from datetime import datetime


class WorkingMemory:
    def __init__(self):
        self.items = {}

    def set(self, key: str, value):
        self.items[key] = {
            "key": key,
            "value": value,
            "updated": datetime.utcnow().isoformat(),
        }
        return self.items[key]

    def get(self, key: str):
        return self.items.get(key)

    def delete(self, key: str):
        return self.items.pop(key, None)

    def list(self):
        return list(self.items.values())

    def status(self):
        return {
            "type": "working",
            "items": len(self.items),
            "ready": True,
        }
