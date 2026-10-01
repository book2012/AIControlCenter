"""Test-owned Caddy documents shared by classification and adapter regressions."""
from __future__ import annotations

import json
from pathlib import Path

from core.deployment.adapters.macos.repository import RepositoryFileReader

ROOT = Path(__file__).resolve().parents[2]
CADDY_PATH = "ops/macos/caddy/Caddyfile"
POLICY_PATH = "config/deployment/caddy-site-policy.json"
INGRESS_PATH = "config/deployment/ingress.json"
PRODUCTION = (ROOT / "tests/fixtures/deployment/dev-ingress-production.Caddyfile").read_text()
GLOBALS, PRODUCTION_SITE = PRODUCTION.split("bokstory.duckdns.org", 1)
PRODUCTION_SITE = "bokstory.duckdns.org" + PRODUCTION_SITE
POLICY_TEXT = (ROOT / POLICY_PATH).read_text()
INGRESS_TEXT = (ROOT / "tests/fixtures/deployment/ingress-contract.json").read_text()
INGRESS = json.loads(INGRESS_TEXT)
# Synthetic test data; never copied from the live-referenced Caddyfile.
AUTH_VALUE = "$" + "2a" + "$" + "12" + "$" + "A" * 53
AUTH = "        basic_auth bcrypt {\n            fixture_user " + AUTH_VALUE + "\n        }\n"
PROXY = "        reverse_proxy 127.0.0.1:18080\n"


def preview_site():
    site = PRODUCTION_SITE.replace("bokstory.duckdns.org", "dev.bokstory.duckdns.org", 1)
    site = site.replace("strict-origin-when-cross-origin", "no-referrer")
    site = site.replace("        -Server", '        X-Robots-Tag "noindex, nofollow, noarchive"\n        -Server')
    site = site.replace('        respond /__aicontrolcenter_ingress_health "ok" 200\n', "")
    site = site.replace('        respond /healthz "ok" 200\n', "")
    return site.replace("        reverse_proxy 127.0.0.1:58082\n", AUTH + PROXY)


PREVIEW = preview_site()
GUARDED = PRODUCTION + "\n" + PREVIEW
UNGUARDED = (PRODUCTION + PREVIEW[:PREVIEW.index("    # Private Control Plane")]
             + AUTH + "    reverse_proxy 127.0.0.1:18080\n}\n")


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
