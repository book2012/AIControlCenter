from __future__ import annotations

import json
import os
import plistlib
import tempfile
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[3]
)
DEFAULT_POLICY_PATH = (
    REPOSITORY_ROOT
    / "config/"
    "governance_operations_scheduler_policy.json"
)


class SchedulerPolicyError(ValueError):
    """Raised when scheduler policy is unsafe."""


def load_policy(
    path: Path = DEFAULT_POLICY_PATH,
) -> dict[str, Any]:
    document = json.loads(
        path.read_text(encoding="utf-8")
    )
    validate_policy(document)
    return document


def validate_policy(
    document: dict[str, Any],
) -> None:
    if document.get("schema_version") != 1:
        raise SchedulerPolicyError(
            "unsupported policy version"
        )

    if document.get("owner") != "AIControlCenter":
        raise SchedulerPolicyError(
            "policy owner must be AIControlCenter"
        )

    if document.get("timezone") != "Asia/Seoul":
        raise SchedulerPolicyError(
            "timezone must be Asia/Seoul"
        )

    expected_safety = {
        "automatic_catch_up": False,
        "automatic_remediation": False,
        "automatic_restore": False,
        "automatic_retry": False,
        "disabled_by_default": True,
        "keep_alive": False,
        "run_at_load": False,
    }

    if document.get("safety") != expected_safety:
        raise SchedulerPolicyError(
            "unsafe scheduler policy"
        )

    definitions = document.get("definitions")

    if (
        not isinstance(definitions, list)
        or len(definitions) != 2
    ):
        raise SchedulerPolicyError(
            "exactly two definitions are required"
        )

    expected_operations = {
        "governance_audit_snapshot",
        "sqlite_online_backup_verification",
    }
    operations: set[str] = set()
    labels: set[str] = set()
    calendars: set[
        tuple[tuple[str, int], ...]
    ] = set()

    for definition in definitions:
        operation = definition.get("operation")
        label = definition.get("label")
        calendar = definition.get("calendar")

        if operation not in expected_operations:
            raise SchedulerPolicyError(
                "unsupported operation"
            )

        if (
            not isinstance(label, str)
            or not label.startswith(
                "com.aicontrolcenter."
            )
        ):
            raise SchedulerPolicyError(
                "invalid launchd label"
            )

        if not isinstance(calendar, dict):
            raise SchedulerPolicyError(
                "calendar must be an object"
            )

        allowed_keys = {
            "Weekday",
            "Hour",
            "Minute",
        }

        if not set(calendar) <= allowed_keys:
            raise SchedulerPolicyError(
                "unsupported calendar field"
            )

        hour = calendar.get("Hour")
        minute = calendar.get("Minute")
        weekday = calendar.get("Weekday")

        if (
            not isinstance(hour, int)
            or isinstance(hour, bool)
            or not 0 <= hour <= 23
        ):
            raise SchedulerPolicyError(
                "invalid calendar hour"
            )

        if (
            not isinstance(minute, int)
            or isinstance(minute, bool)
            or not 0 <= minute <= 59
        ):
            raise SchedulerPolicyError(
                "invalid calendar minute"
            )

        if weekday is not None and (
            not isinstance(weekday, int)
            or isinstance(weekday, bool)
            or not 0 <= weekday <= 7
        ):
            raise SchedulerPolicyError(
                "invalid calendar weekday"
            )

        calendar_key = tuple(
            sorted(calendar.items())
        )

        if operation in operations:
            raise SchedulerPolicyError(
                "duplicate operation"
            )

        if label in labels:
            raise SchedulerPolicyError(
                "duplicate label"
            )

        if calendar_key in calendars:
            raise SchedulerPolicyError(
                "duplicate calendar"
            )

        operations.add(operation)
        labels.add(label)
        calendars.add(calendar_key)

    if operations != expected_operations:
        raise SchedulerPolicyError(
            "required operations are missing"
        )


def activation_directory(
    path: Path,
) -> bool:
    resolved = path.expanduser().resolve()

    protected = (
        (
            Path.home()
            / "Library/LaunchAgents"
        ).resolve(),
        Path("/Library/LaunchAgents"),
        Path("/Library/LaunchDaemons"),
        Path(
            "/System/Library/LaunchAgents"
        ),
        Path(
            "/System/Library/LaunchDaemons"
        ),
    )

    return any(
        resolved == candidate
        or candidate in resolved.parents
        for candidate in protected
    )


def render_documents(
    document: dict[str, Any],
    *,
    repository_root: Path,
    python_executable: Path,
    log_directory: Path,
) -> dict[str, dict[str, Any]]:
    validate_policy(document)

    if not repository_root.is_dir():
        raise SchedulerPolicyError(
            "repository root does not exist"
        )

    if not python_executable.is_file():
        raise SchedulerPolicyError(
            "Python executable does not exist"
        )

    rendered: dict[
        str,
        dict[str, Any],
    ] = {}

    for definition in document["definitions"]:
        label = definition["label"]
        operation = definition["operation"]

        rendered[label] = {
            "Disabled": True,
            "EnvironmentVariables": {
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            "KeepAlive": False,
            "Label": label,
            "ProcessType": "Background",
            "ProgramArguments": [
                str(
                    python_executable.resolve()
                ),
                "-m",
                document["runner"]["module"],
                "--operation",
                operation,
                "--once",
                "--json",
            ],
            "RunAtLoad": False,
            "StandardErrorPath": str(
                log_directory
                / f"{label}.stderr.log"
            ),
            "StandardOutPath": str(
                log_directory
                / f"{label}.stdout.log"
            ),
            "StartCalendarInterval": (
                definition["calendar"]
            ),
            "WorkingDirectory": str(
                repository_root.resolve()
            ),
        }

    return rendered


def write_documents(
    document: dict[str, Any],
    *,
    output_directory: Path,
    repository_root: Path,
    python_executable: Path,
    log_directory: Path,
) -> list[Path]:
    resolved_output = (
        output_directory
        .expanduser()
        .resolve()
    )

    if activation_directory(
        resolved_output
    ):
        raise SchedulerPolicyError(
            "renderer cannot install or "
            "activate launchd jobs"
        )

    rendered = render_documents(
        document,
        repository_root=repository_root,
        python_executable=python_executable,
        log_directory=log_directory,
    )

    resolved_output.mkdir(
        parents=True,
        exist_ok=True,
    )
    written: list[Path] = []

    for label, plist_document in sorted(
        rendered.items()
    ):
        target = (
            resolved_output
            / f"{label}.plist"
        )
        payload = plistlib.dumps(
            plist_document,
            fmt=plistlib.FMT_XML,
            sort_keys=True,
        )

        descriptor, temporary_name = (
            tempfile.mkstemp(
                dir=str(resolved_output),
                prefix=f".{target.name}.",
                suffix=".tmp",
            )
        )
        temporary = Path(
            temporary_name
        )

        try:
            with os.fdopen(
                descriptor,
                "wb",
            ) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            parsed = plistlib.loads(
                temporary.read_bytes()
            )

            if parsed != plist_document:
                raise SchedulerPolicyError(
                    "rendered plist verification "
                    "failed"
                )

            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()

        written.append(target)

    return written
