"""Test-owned Caddy documents shared by classification and adapter regressions."""
from __future__ import annotations

import json
from pathlib import Path
import re

from core.deployment.adapters.macos.repository import RepositoryFileReader

ROOT = Path(__file__).resolve().parents[2]
CADDY_PATH = "ops/macos/caddy/Caddyfile"
POLICY_PATH = "config/deployment/caddy-site-policy.json"
INGRESS_PATH = "config/deployment/ingress.json"
CADDY_SOURCE = (ROOT / CADDY_PATH).read_text()
GLOBALS, remainder = CADDY_SOURCE.split("bokstory.duckdns.org", 1)
production_body, preview_body = remainder.split("\ndev.bokstory.duckdns.org", 1)
PRODUCTION = GLOBALS + "bokstory.duckdns.org" + production_body
PRODUCTION_SITE = "bokstory.duckdns.org" + production_body
PREVIEW_SOURCE = "dev.bokstory.duckdns.org" + preview_body
POLICY_TEXT = (ROOT / POLICY_PATH).read_text()
INGRESS_TEXT = (ROOT / "tests/fixtures/deployment/ingress-contract.json").read_text()
INGRESS = json.loads(INGRESS_TEXT)
# Synthetic test data; never copied from the live-referenced Caddyfile.
AUTH_VALUE = "$" + "2a" + "$" + "12" + "$" + "A" * 53
AUTH = "        basic_auth bcrypt {\n            fixture_user " + AUTH_VALUE + "\n        }\n"
PROXY = "        reverse_proxy 127.0.0.1:18080\n"


def preview_site():
    return re.sub(r"        basic_auth \{\n.*?\n        \}\n", AUTH, PREVIEW_SOURCE, count=1, flags=re.DOTALL)


PREVIEW = preview_site()
GUARDED = PRODUCTION + "\n" + PREVIEW
UNGUARDED = GLOBALS + "\n" + PREVIEW.replace(AUTH, "")


class CaddyFixtureFiles(RepositoryFileReader):
    """Overlay only test-owned Caddy/policy/contract data on other repo inputs."""

    def __init__(self, text=PRODUCTION, *, overrides=None):
        super().__init__(ROOT)
        self.overrides = {CADDY_PATH: text, POLICY_PATH: POLICY_TEXT, INGRESS_PATH: INGRESS_TEXT}
        self.overrides.update(overrides or {})
        self.reads = []

    def read_text(self, path):
        self.reads.append(path)
        if path in self.overrides:
            value = self.overrides[path]
            if isinstance(value, Exception):
                raise value
            return value
        return super().read_text(path)
