from pathlib import Path


class MarkdownLoader:
    def load(self, path: str):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        return {
            "name": path.name,
            "path": str(path),
            "content": path.read_text(encoding="utf-8"),
            "lines": len(path.read_text(encoding="utf-8").splitlines()),
        }
