import os


class ConfigValidation:
    REQUIRED = {
        "OPENAI_API_KEY": False,
        "TELEGRAM_BOT_TOKEN": False,
        "TELEGRAM_CHAT_ID": False,
    }

    def validate(self):
        items = {}

        for key, strictly_required in self.REQUIRED.items():
            configured = bool(os.getenv(key))

            items[key] = {
                "configured": configured,
                "required": strictly_required,
            }

        valid = all(
            item["configured"]
            for item in items.values()
            if item["required"]
        )

        return {
            "valid": valid,
            "items": items,
        }
