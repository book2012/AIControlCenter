from core.knowledge.index import KnowledgeIndex


class KnowledgeSearch:
    def __init__(self, index: KnowledgeIndex | None = None):
        self.index = index or KnowledgeIndex()
        self.index.build()

    def search(self, query: str):
        words = [
            word.lower()
            for word in query.replace("/", " ").split()
            if word.strip()
        ]

        results = []

        for name, document in self.index.documents.items():
            content = document["content"].lower()
            score = sum(1 for word in words if word in content)

            if score > 0:
                results.append({
                    "name": name,
                    "path": document["path"],
                    "score": score,
                    "lines": document["lines"],
                })

        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

    def status(self):
        return {
            "documents": len(self.index.documents),
            "ready": True,
        }
