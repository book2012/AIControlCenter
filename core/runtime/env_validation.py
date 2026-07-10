from pathlib import Path


class EnvironmentTemplateValidator:
    REQUIRED_KEYS = {
        "AI_PROVIDER",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "GOOGLE_API_KEY",
        "GOOGLE_MODEL",
        "GITHUB_TOKEN",
        "NOTION_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "LOG_LEVEL",
        "TIMEZONE",
    }

    SECRET_KEYS = {
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "GITHUB_TOKEN",
        "NOTION_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "WORDPRESS_APP_PASSWORD",
    }

    def __init__(self, path: str = ".env.example"):
        self.path = Path(path)

    def parse(self):
        values = {}

        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()

        return values

    def validate(self):
        if not self.path.exists():
            return {
                "valid": False,
                "missing_file": True,
                "missing_keys": sorted(self.REQUIRED_KEYS),
                "exposed_secrets": [],
            }

        values = self.parse()

        missing = sorted(self.REQUIRED_KEYS - values.keys())
        exposed = sorted(
            key
            for key in self.SECRET_KEYS
            if values.get(key)
        )

        return {
            "valid": not missing and not exposed,
            "missing_file": False,
            "missing_keys": missing,
            "exposed_secrets": exposed,
        }
