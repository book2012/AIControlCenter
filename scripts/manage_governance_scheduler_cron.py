#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "config/governance_scheduler_cron.json"
)

BEGIN_MARKER = (
    "# BEGIN AICONTROLCENTER "
    "GOVERNANCE SCHEDULER"
)
END_MARKER = (
    "# END AICONTROLCENTER "
    "GOVERNANCE SCHEDULER"
)


class CronManagerError(RuntimeError):
    pass


def normalize(text: str) -> str:
    stripped = text.rstrip()

    if not stripped:
        return ""

    return stripped + "\n"


def load_config() -> dict[str, Any]:
    document = json.loads(
        CONFIG_PATH.read_text(
            encoding="utf-8"
        )
    )

    if document.get("schema_version") != 1:
        raise CronManagerError(
            "unsupported schema version"
        )

    if document.get("owner") != "AIControlCenter":
        raise CronManagerError(
            "invalid owner"
        )

    if document.get(
        "deployment_method"
    ) != "user_crontab":
        raise CronManagerError(
            "unsupported deployment method"
        )

    if document.get("timezone") != "Asia/Seoul":
        raise CronManagerError(
            "invalid timezone"
        )

    expected_safety = {
        "automatic_catch_up": False,
        "automatic_remediation": False,
        "automatic_restore": False,
        "automatic_retry": False,
    }

    if document.get("safety") != expected_safety:
        raise CronManagerError(
            "unsafe scheduler policy"
        )

    definitions = document.get(
        "definitions"
    )

    if (
        not isinstance(definitions, list)
        or len(definitions) != 2
    ):
        raise CronManagerError(
            "exactly two definitions required"
        )

    expected = {
        "governance_audit_snapshot",
        "sqlite_online_backup_verification",
    }

    if {
        item.get("operation")
        for item in definitions
    } != expected:
        raise CronManagerError(
            "operation set mismatch"
        )

    return document


def render_shell_command(
    definition: dict[str, Any],
    config: dict[str, Any],
) -> str:
    repository = shlex.quote(
        config["repository"]
    )
    python = shlex.quote(
        config["python"]
    )
    module = shlex.quote(
        config["runner_module"]
    )
    operation = shlex.quote(
        definition["operation"]
    )
    stdout_log = shlex.quote(
        definition["stdout_log"]
    )
    stderr_log = shlex.quote(
        definition["stderr_log"]
    )

    return (
        f"cd {repository} && "
        "PYTHONDONTWRITEBYTECODE=1 "
        f"{python} -m {module} "
        f"--operation {operation} "
        "--once --json "
        f">> {stdout_log} "
        f"2>> {stderr_log}"
    )


def render_block(
    config: dict[str, Any],
) -> str:
    lines = [
        BEGIN_MARKER,
        "SHELL=/bin/zsh",
        "HOME=/Users/kyouhan",
        (
            "PATH=/usr/local/bin:/usr/bin:"
            "/bin:/usr/sbin:/sbin"
        ),
        "TZ=Asia/Seoul",
        'MAILTO=""',
    ]

    for definition in config[
        "definitions"
    ]:
        lines.append(
            definition["cron"]
            + " "
            + render_shell_command(
                definition,
                config,
            )
        )

    lines.append(END_MARKER)

    return "\n".join(lines) + "\n"


def strip_managed_block(
    text: str,
) -> str:
    lines = text.splitlines()
    begin_indexes = [
        index
        for index, line in enumerate(lines)
        if line == BEGIN_MARKER
    ]
    end_indexes = [
        index
        for index, line in enumerate(lines)
        if line == END_MARKER
    ]

    if (
        not begin_indexes
        and not end_indexes
    ):
        return normalize(text)

    if (
        len(begin_indexes) != 1
        or len(end_indexes) != 1
        or begin_indexes[0]
        >= end_indexes[0]
    ):
        raise CronManagerError(
            "malformed managed block"
        )

    remaining = (
        lines[:begin_indexes[0]]
        + lines[end_indexes[0] + 1:]
    )

    while (
        remaining
        and not remaining[-1].strip()
    ):
        remaining.pop()

    return (
        "\n".join(remaining) + "\n"
        if remaining
        else ""
    )


def compose_install(
    existing: str,
    block: str,
) -> str:
    base = strip_managed_block(
        existing
    ).rstrip()

    if not base:
        return normalize(block)

    return (
        base
        + "\n\n"
        + normalize(block)
    )


def read_crontab() -> tuple[str, bool]:
    completed = subprocess.run(
        ["/usr/bin/crontab", "-l"],
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode == 0:
        return normalize(
            completed.stdout
        ), True

    if (
        completed.returncode == 1
        and not completed.stdout.strip()
        and "no crontab"
        in completed.stderr.lower()
    ):
        return "", False

    raise CronManagerError(
        completed.stderr.strip()
        or completed.stdout.strip()
    )


def write_crontab(text: str) -> None:
    completed = subprocess.run(
        ["/usr/bin/crontab", "-"],
        check=False,
        capture_output=True,
        text=True,
        input=normalize(text),
    )

    if completed.returncode != 0:
        raise CronManagerError(
            completed.stderr.strip()
            or completed.stdout.strip()
        )


def remove_crontab() -> None:
    completed = subprocess.run(
        ["/usr/bin/crontab", "-r"],
        check=False,
        capture_output=True,
        text=True,
    )

    if (
        completed.returncode != 0
        and "no crontab"
        not in (
            completed.stderr
            + completed.stdout
        ).lower()
    ):
        raise CronManagerError(
            completed.stderr.strip()
            or completed.stdout.strip()
        )


def status_document() -> dict[str, Any]:
    config = load_config()
    current, existed = read_crontab()
    block = render_block(config)
    expected = compose_install(
        strip_managed_block(current),
        block,
    )

    installed = (
        BEGIN_MARKER in current
        and END_MARKER in current
        and normalize(current)
        == normalize(expected)
    )

    return {
        "crontab_exists": existed,
        "deployment_method": (
            "user_crontab"
        ),
        "installed": installed,
        "managed_block": (
            config["managed_block"]
        ),
        "result": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        choices=(
            "render",
            "status",
            "install",
            "uninstall",
        ),
        required=True,
    )
    parser.add_argument(
        "--json",
        action="store_true",
    )
    arguments = parser.parse_args()

    config = load_config()

    if arguments.action == "render":
        result = {
            "block": render_block(config),
            "installed": False,
            "result": "PASS",
        }
    elif arguments.action == "status":
        result = status_document()
    else:
        if os.environ.get(
            "AICONTROLCENTER_CRON_WRITE_APPROVED"
        ) != "YES":
            raise CronManagerError(
                "explicit write approval required"
            )

        current, existed = read_crontab()

        if arguments.action == "install":
            updated = compose_install(
                current,
                render_block(config),
            )
            write_crontab(updated)
        else:
            updated = strip_managed_block(
                current
            )

            if updated:
                write_crontab(updated)
            elif existed:
                remove_crontab()

        result = status_document()

        if arguments.action == "install":
            if not result["installed"]:
                raise CronManagerError(
                    "install verification failed"
                )
        else:
            if result["installed"]:
                raise CronManagerError(
                    "uninstall verification failed"
                )

        result["action"] = arguments.action

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
