from pathlib import Path


class LogsService:
    def __init__(self, log_root: str = "/mnt/storage/Backup/logs"):
        self.log_root = Path(log_root)

    def recent(self, limit: int = 10):
        if not self.log_root.exists():
            return {
                "root": str(self.log_root),
                "exists": False,
                "logs": [],
            }

        files = [
            item
            for item in self.log_root.iterdir()
            if item.is_file()
        ]

        files = sorted(
            files,
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:limit]

        return {
            "root": str(self.log_root),
            "exists": True,
            "logs": [
                {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                }
                for item in files
            ],
        }

    def format_text(self):
        result = self.recent()

        if not result["exists"]:
            return f"📄 Logs\nRoot not found: {result['root']}"

        if not result["logs"]:
            return f"📄 Logs\nNo logs found in {result['root']}"

        lines = [
            "📄 Recent Logs",
            f"Root: {result['root']}",
            "",
        ]

        for item in result["logs"]:
            lines.append(f"- {item['name']} ({item['size']} bytes)")

        return "\n".join(lines)
