from __future__ import annotations

import argparse
import dataclasses
import enum
import fcntl
import importlib
import json
import os
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID, uuid4


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[3]
)
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "config/governance_operations_runner.json"
)
DEFAULT_LOCK_DIRECTORY = (
    Path.home()
    / "Library/Application Support/"
    "AIControlCenter/run/"
    "governance-operations"
)


class OperationRunnerError(RuntimeError):
    """Raised when runner policy is invalid."""


def load_config(
    path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    document = json.loads(
        path.read_text(encoding="utf-8")
    )

    if document.get("schema_version") != 1:
        raise OperationRunnerError(
            "unsupported configuration version"
        )

    if document.get("owner") != "AIControlCenter":
        raise OperationRunnerError(
            "runner owner must be AIControlCenter"
        )

    expected_safety = {
        "automatic_catch_up": False,
        "automatic_remediation": False,
        "automatic_restore": False,
        "automatic_retry": False,
        "launchd_activation_enabled": False,
        "scheduling_enabled": False,
    }

    if document.get("safety") != expected_safety:
        raise OperationRunnerError(
            "unsafe runner policy"
        )

    expected_operations = {
        "governance_audit_snapshot",
        "sqlite_online_backup_verification",
    }

    if (
        set(document.get("operations", []))
        != expected_operations
    ):
        raise OperationRunnerError(
            "unsupported operation configuration"
        )

    return document


def _symbol(
    module_name: str,
    symbol_name: str,
) -> Any:
    module = importlib.import_module(
        module_name
    )
    return getattr(module, symbol_name)


def validate_composition_symbols(
    path: Path = CONFIG_PATH,
) -> None:
    document = load_config(path)

    specifications = [
        *document["composition"].values(),
        document["dispatch"]["service"],
        document["dispatch"]["command"],
        document["dispatch"][
            "operation_enum"
        ],
    ]

    for specification in specifications:
        target = _symbol(
            specification["module"],
            specification["class"],
        )

        if not callable(target):
            raise OperationRunnerError(
                "composition symbol "
                "is not callable"
            )


def composition_descriptor(
    path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    return load_config(path)["composition"]


def _runtime_context(
    document: dict[str, Any],
) -> dict[str, Any]:
    paths = document["paths"]

    return {
        "production_database": Path(
            os.environ.get(
                paths[
                    "production_database_environment"
                ],
                paths[
                    "production_database_default"
                ],
            )
        ).expanduser(),
    }


def _construct(
    specification: dict[str, Any],
    context: dict[str, Any],
) -> Any:
    target = _symbol(
        specification["module"],
        specification["class"],
    )
    bindings = specification["bindings"]

    positional = [
        context[token]
        for token in bindings["positional"]
    ]
    keyword = {
        name: context[token]
        for name, token
        in bindings["keyword"].items()
    }

    return target(
        *positional,
        **keyword,
    )


def build_service(
    path: Path = CONFIG_PATH,
) -> Any:
    document = load_config(path)
    context = _runtime_context(document)

    for role in (
        "repository",
        "clock",
        "snapshot_executor",
        "backup_verifier",
    ):
        context[role] = _construct(
            document["composition"][role],
            context,
        )

    service_specification = document[
        "dispatch"
    ]["service"]
    service_class = _symbol(
        service_specification["module"],
        service_specification["class"],
    )

    keyword = {
        name: context[token]
        for name, token
        in service_specification[
            "bindings"
        ].items()
    }

    return service_class(**keyword)


def _normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _normalize(
            dataclasses.asdict(value)
        )

    if isinstance(value, enum.Enum):
        return _normalize(value.value)

    if isinstance(
        value,
        (
            datetime,
            date,
            UUID,
            Path,
        ),
    ):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): _normalize(child)
            for key, child
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
            frozenset,
        ),
    ):
        return [
            _normalize(child)
            for child in value
        ]

    if (
        hasattr(value, "to_dict")
        and callable(value.to_dict)
    ):
        return _normalize(
            value.to_dict()
        )

    if (
        hasattr(value, "as_dict")
        and callable(value.as_dict)
    ):
        return _normalize(
            value.as_dict()
        )

    return value


def _operation_value(
    operation_enum: Any,
    operation: str,
) -> Any:
    try:
        return operation_enum(operation)
    except (TypeError, ValueError):
        for member in operation_enum:
            if (
                getattr(member, "value", None)
                == operation
            ):
                return member

    raise OperationRunnerError(
        f"unsupported operation enum: "
        f"{operation}"
    )


@contextmanager
def operation_lock(
    operation: str,
    directory: Path,
) -> Iterator[bool]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )
    lock_path = directory / (
        f"{operation}.lock"
    )

    with lock_path.open(
        "a+",
        encoding="utf-8",
    ) as handle:
        try:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX
                | fcntl.LOCK_NB,
            )
        except BlockingIOError:
            yield False
            return

        try:
            yield True
        finally:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_UN,
            )


def execute_once(
    operation: str,
    *,
    config_path: Path = CONFIG_PATH,
    lock_directory: Path = (
        DEFAULT_LOCK_DIRECTORY
    ),
    service_override: Any | None = None,
    scheduled_for: datetime | None = None,
    dispatch_id: UUID | None = None,
) -> dict[str, Any]:
    document = load_config(config_path)

    if operation not in document["operations"]:
        raise OperationRunnerError(
            f"unsupported operation: "
            f"{operation}"
        )

    with operation_lock(
        operation,
        lock_directory,
    ) as acquired:
        if not acquired:
            return {
                "automatic_retry": False,
                "operation": operation,
                "reason": (
                    "operation-already-running"
                ),
                "result": "SKIP",
            }

        dispatch = document["dispatch"]
        command_class = _symbol(
            dispatch["command"]["module"],
            dispatch["command"]["class"],
        )
        operation_enum = _symbol(
            dispatch[
                "operation_enum"
            ]["module"],
            dispatch[
                "operation_enum"
            ]["class"],
        )

        effective_time = (
            scheduled_for
            or datetime.now(timezone.utc)
        )
        effective_dispatch_id = (
            dispatch_id or uuid4()
        )

        command = command_class(
            job_id=(
                f"runner:{operation}:"
                f"{effective_dispatch_id}"
            ),
            operation=_operation_value(
                operation_enum,
                operation,
            ),
            scheduled_for=effective_time,
            dispatch_id=(
                effective_dispatch_id
            ),
            attempt=1,
        )

        service = (
            service_override
            if service_override is not None
            else build_service(
                config_path
            )
        )
        payload = service.dispatch(command)

        return {
            "automatic_retry": False,
            "dispatch_id": str(
                effective_dispatch_id
            ),
            "operation": operation,
            "payload": _normalize(payload),
            "result": "PASS",
            "scheduled_for": (
                effective_time.isoformat()
            ),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute one AIControlCenter "
            "governance operation."
        )
    )
    parser.add_argument(
        "--operation",
        choices=(
            "governance_audit_snapshot",
            (
                "sqlite_online_backup_"
                "verification"
            ),
        ),
        required=True,
    )
    parser.add_argument(
        "--once",
        action="store_true",
    )
    parser.add_argument(
        "--json",
        action="store_true",
    )
    return parser


def main() -> int:
    arguments = (
        build_parser().parse_args()
    )

    try:
        if not arguments.once:
            raise OperationRunnerError(
                "--once is required"
            )

        if not arguments.json:
            raise OperationRunnerError(
                "--json is required"
            )

        result = execute_once(
            arguments.operation
        )
        return_code = 0

    except Exception as error:
        result = {
            "automatic_retry": False,
            "error": str(error),
            "error_class": (
                type(error).__name__
            ),
            "result": "FAIL",
        }
        return_code = 1

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
