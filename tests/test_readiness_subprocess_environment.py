from __future__ import annotations

import sys
from unittest.mock import Mock, patch

from scripts import readiness_check


def test_readiness_uses_current_python_for_pytest() -> None:
    captured_commands: list[list[str]] = []

    def fake_command_ok(
        command: list[str],
    ) -> bool:
        captured_commands.append(command)
        return True

    healthy_response = Mock()
    healthy_response.status_code = 200

    with (
        patch.object(
            readiness_check,
            "command_ok",
            side_effect=fake_command_ok,
        ),
        patch.object(
            readiness_check.EnvironmentTemplateValidator,
            "validate",
            return_value={"valid": True},
        ),
        patch.object(
            readiness_check.Path,
            "exists",
            return_value=True,
        ),
        patch.object(
            readiness_check.requests,
            "get",
            return_value=healthy_response,
        ),
        patch.object(
            readiness_check.ServiceHealth,
            "status",
            return_value={"healthy": True},
        ),
    ):
        result = readiness_check.main()

    assert result == 0
    assert [
        sys.executable,
        "-m",
        "pytest",
        "-q",
    ] in captured_commands
