from datetime import datetime, timedelta
from uuid import uuid4


class BackupConfirmService:
    def __init__(self):
        self.tokens = {}

    def create_token(self):
        token = str(uuid4())
        expires = datetime.utcnow() + timedelta(minutes=10)

        self.tokens[token] = {
            "token": token,
            "expires": expires,
            "used": False,
        }

        return {
            "token": token,
            "expires": expires.isoformat(),
            "used": False,
        }

    def validate(self, token: str):
        item = self.tokens.get(token)

        if not item:
            return False

        if item["used"]:
            return False

        if datetime.utcnow() > item["expires"]:
            return False

        return True

    def consume(self, token: str):
        if not self.validate(token):
            return False

        self.tokens[token]["used"] = True
        return True

    def format_text(self):
        token = self.create_token()

        return "\n".join([
            "⚠️ Backup Confirm Token",
            "",
            "Backup execution is not started yet.",
            "Use this token only after reviewing the plan.",
            "",
            f"Token: {token['token']}",
            f"Expires: {token['expires']}",
            "",
            "Next command:",
            f"/backup run {token['token']}",
        ])
