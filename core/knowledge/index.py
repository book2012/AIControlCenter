from pathlib import Path

from core.knowledge.loader import MarkdownLoader
from core.knowledge.registry import KnowledgeRegistry


class KnowledgeIndex:
    def __init__(
        self,
        root: str = ".",
        registry: KnowledgeRegistry | None = None,
        loader: MarkdownLoader | None = None,
    ):
        self.root = Path(root)
        self.registry = registry or KnowledgeRegistry()
        self.loader = loader or MarkdownLoader()
        self.documents = {}

    def discover(self):
        candidates = [
            "README.md",
            "MASTER.md",
            "ROADMAP.md",
            "CHANGELOG.md",
            "TODO.md",
            "PROJECT_HISTORY.md",
        ]

        for name in candidates:
            path = self.root / name
            if path.exists():
                self.registry.register(name, str(path))

        docs_dir = self.root / "docs"
        if docs_dir.exists():
            for path in docs_dir.glob("*.md"):
                self.registry.register(path.name, str(path))

        return self.registry.list()

    def build(self):
        self.discover()

        for item in self.registry.list():
            if item["exists"]:
                document = self.loader.load(item["path"])
                self.documents[item["name"]] = document

        return {
            "documents": len(self.documents),
            "items": list(self.documents.keys()),
        }

    def status(self):
        return {
            "documents": len(self.documents),
            "ready": True,
        }
