from datetime import datetime
from uuid import uuid4

from core.automation.executor import AutomationExecutor


class AutomationQueue:
    def __init__(self, executor: AutomationExecutor | None = None):
        self.executor = executor or AutomationExecutor()
        self.items = {}

    def submit(self, action: str):
        item_id = str(uuid4())

        item = {
            "id": item_id,
            "action": action,
            "status": "PENDING",
            "created": datetime.utcnow().isoformat(),
            "finished": None,
            "result": None,
        }

        self.items[item_id] = item
        return item

    def run(self, item_id: str):
        item = self.items[item_id]
        item["status"] = "RUNNING"

        result = self.executor.execute(item["action"])

        item["result"] = result
        item["finished"] = datetime.utcnow().isoformat()
        item["status"] = "FINISHED" if result.get("executed") else "BLOCKED"

        return item

    def get(self, item_id: str):
        return self.items[item_id]

    def list(self):
        return list(self.items.values())
