from __future__ import annotations

import sys
from unittest.mock import patch

from scripts import readiness_check


def test_readiness_uses_current_python_for_pytest() -> None:
    captured_commands: list[list[str]] = []

    def fake_command_ok(command: list[str]) -> bool:
        captured_commands.append(command)
        return True

    with patch.object(
        readiness_check,
        "command_ok",
        side_effect=fake_command_ok,
    ):
        with patch.object(
            readiness_check.EnvironmentTemplateValidator,
            "validate",
            return_value={"valid": True},
        ):
            result = readiness_check.main()

    assert result == 0
    assert [sys.executable, "-m", "pytest", "-q"] in captured_commands
