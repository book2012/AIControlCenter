from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


class ConfigLoader:
    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)

    def load(self) -> Dict[str, Any]:
        loaded = False

        if self.env_path.exists():
            loaded = load_dotenv(self.env_path)

        return {
            "env_path": str(self.env_path),
            "exists": self.env_path.exists(),
            "loaded": loaded,
        }
