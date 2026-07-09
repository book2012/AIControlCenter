from pathlib import Path

from core.config.loader import ConfigLoader


def test_config_loader_missing_env(tmp_path):
    env_path = tmp_path / ".env"

    result = ConfigLoader(str(env_path)).load()

    assert result["exists"] is False
    assert result["loaded"] is False


def test_config_loader_existing_env(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("TEST_CONFIG_LOADER=ok\n")

    result = ConfigLoader(str(env_path)).load()

    assert result["exists"] is True
