from pathlib import Path


class KnowledgeRegistry:
    def __init__(self):
        self._documents = {}

    def register(self, name: str, path: str):
        self._documents[name] = Path(path)

    def unregister(self, name: str):
        self._documents.pop(name, None)

    def list(self):
        return [
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
            }
            for name, path in sorted(self._documents.items())
        ]

    def count(self):
        return len(self._documents)

    def status(self):
        docs = self.list()

        return {
            "documents": len(docs),
            "available": sum(d["exists"] for d in docs),
        }
