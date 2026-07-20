import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_state(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "sha256": sha256(path),
    }


def build_snapshot() -> dict:
    return {
        "schema_version": "1.0",
        "service_id": "ollama",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "execution_enabled": False,
        "targets": {
            "binary": file_state(Path("/opt/homebrew/bin/ollama")),
            "plist": file_state(Path("/Library/LaunchDaemons/com.aicontrolcenter.ollama.plist")),
            "environment": file_state(Path("/Library/Application Support/AIControlCenter/ollama.env")),
            "models": file_state(Path.home() / "Library/Application Support/Ollama/models"),
        },
        "rollback": {
            "required": True,
            "preserve_models": True,
            "restore_binary": True,
            "restore_plist": True,
            "restore_environment": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    snapshot = build_snapshot()
    payload = json.dumps(snapshot, indent=2, sort_keys=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
