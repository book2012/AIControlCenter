from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "config/governance_scheduler_cron.json"
)
MANAGER_PATH = (
    REPOSITORY_ROOT
    / "scripts/manage_governance_scheduler_cron.py"
)

SPEC = importlib.util.spec_from_file_location(
    "governance_scheduler_cron_manager",
    MANAGER_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None

MANAGER = importlib.util.module_from_spec(
    SPEC
)
SPEC.loader.exec_module(MANAGER)


def test_explicit_headless_cadence():
    config = json.loads(
        CONFIG_PATH.read_text(
            encoding="utf-8"
        )
    )
    definitions = {
        item["operation"]: item
        for item in config["definitions"]
    }

    assert (
        definitions[
            "governance_audit_snapshot"
        ]["cron"]
        == "10 3 * * *"
    )
    assert (
        definitions[
            "sqlite_online_backup_verification"
        ]["cron"]
        == "10 4 * * 0"
    )
    assert config["timezone"] == "Asia/Seoul"


def test_unsafe_automation_disabled():
    config = MANAGER.load_config()

    assert config["safety"] == {
        "automatic_catch_up": False,
        "automatic_remediation": False,
        "automatic_restore": False,
        "automatic_retry": False,
    }


def test_rendered_block_is_json_one_shot():
    config = MANAGER.load_config()
    block = MANAGER.render_block(config)

    assert "--once --json" in block
    assert block.count("--operation") == 2
    assert "launchctl" not in block
    assert "SMAppService" not in block
    assert "retry" not in block.lower()


def test_install_preserves_unrelated_entries():
    existing = (
        "0 1 * * * /usr/bin/true\n"
    )
    block = (
        MANAGER.render_block(
            MANAGER.load_config()
        )
    )
    installed = MANAGER.compose_install(
        existing,
        block,
    )

    assert existing.strip() in installed
    assert MANAGER.BEGIN_MARKER in installed
    assert MANAGER.END_MARKER in installed


def test_uninstall_restores_original_content():
    original = (
        "0 1 * * * /usr/bin/true\n"
    )
    block = MANAGER.render_block(
        MANAGER.load_config()
    )
    installed = MANAGER.compose_install(
        original,
        block,
    )
    restored = MANAGER.strip_managed_block(
        installed
    )

    assert restored == original
