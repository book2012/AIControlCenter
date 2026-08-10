#!/usr/bin/env python3
"""Validate and inject external provider credentials without exposing values."""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
from dataclasses import asdict, dataclass
from pathlib import Path
import stat
import sys
from typing import Mapping, Sequence


DEFAULT_SECRET_ROOT = Path(
    "/Users/kyouhan/Library/Application Support/AIControlCenter/secrets"
)
PROVIDERS = {
    "openai": ("openai-api-key", "OPENAI_API_KEY", True),
    "claude": ("anthropic-api-key", "ANTHROPIC_API_KEY", True),
    "ollama": (None, None, False),
}
FAILURE = "Provider credential validation failed"
EXPECTED_UID = pwd.getpwnam("kyouhan").pw_uid
EXPECTED_GID = grp.getgrnam("staff").gr_gid


class SecretValidationError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(FAILURE)


@dataclass(frozen=True)
class ValidationResult:
    schema_version: int
    operation: str
    provider: str
    environment_variable: str | None
    secret_path: str | None
    mandatory: bool
    directory_valid: bool
    exists: bool
    regular_file: bool
    owner_valid: bool
    group_valid: bool
    mode_valid: bool
    readable: bool
    nonempty: bool
    format_valid: bool
    credential_value_exposed: bool
    ready: bool


def _result(provider: str, root: Path, *, read_value: bool) -> tuple[ValidationResult, str | None]:
    if provider not in PROVIDERS:
        raise SecretValidationError()
    filename, variable, mandatory = PROVIDERS[provider]
    if not mandatory:
        return ValidationResult(1, "provider-secret-validation", provider, variable, None,
            False, True, False, False, True, True, True, True, True, True, False, True), None

    path = root / str(filename)
    directory = exists = regular = owner = group = mode = readable = nonempty = shape = False
    credential: str | None = None
    try:
        root_info = root.lstat()
        directory = (
            stat.S_ISDIR(root_info.st_mode)
            and not root.is_symlink()
            and root_info.st_uid == EXPECTED_UID
            and root_info.st_gid == EXPECTED_GID
            and stat.S_IMODE(root_info.st_mode) == 0o700
        )
        info = path.lstat()
        exists = True
        regular = stat.S_ISREG(info.st_mode) and not path.is_symlink()
        owner = info.st_uid == EXPECTED_UID
        group = info.st_gid == EXPECTED_GID
        mode = stat.S_IMODE(info.st_mode) == 0o600
        if directory and regular and owner and group and mode:
            data = path.read_bytes()
            readable = True
            nonempty = bool(data)
            shape = (
                nonempty
                and b"\x00" not in data
                and data.count(b"\n") <= 1
                and (b"\n" not in data or data.endswith(b"\n"))
                and b"\r" not in data
            )
            if shape:
                raw = data[:-1] if data.endswith(b"\n") else data
                try:
                    value = raw.decode("utf-8")
                except UnicodeDecodeError:
                    shape = False
                else:
                    shape = bool(value) and value == value.strip()
                    if shape and read_value:
                        credential = value
    except (FileNotFoundError, PermissionError, OSError):
        pass

    ready = all((directory, exists, regular, owner, group, mode, readable, nonempty, shape))
    return ValidationResult(1, "provider-secret-validation", provider, variable, str(path),
        mandatory, directory, exists, regular, owner, group, mode, readable, nonempty, shape, False, ready), credential


def validate(provider: str, root: Path = DEFAULT_SECRET_ROOT) -> ValidationResult:
    return _result(provider, root, read_value=False)[0]


def execute(provider: str, command: Sequence[str], root: Path = DEFAULT_SECRET_ROOT,
            environment: Mapping[str, str] | None = None) -> None:
    result, credential = _result(provider, root, read_value=True)
    if not result.ready or (result.mandatory and credential is None):
        raise SecretValidationError()
    child_environment = dict(os.environ if environment is None else environment)
    if result.environment_variable is not None:
        child_environment[result.environment_variable] = credential or ""
    os.execvpe(command[0], list(command), child_environment)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("validate", "exec"))
    parser.add_argument("--provider", required=True)
    parser.add_argument("--secret-root", type=Path, default=DEFAULT_SECRET_ROOT)
    args, command = parser.parse_known_args()
    try:
        if args.action == "validate":
            if command:
                raise SecretValidationError()
            result = validate(args.provider, args.secret_root)
            print(json.dumps(asdict(result), sort_keys=True))
            return 0 if result.ready else 78
        command = command[1:] if command[:1] == ["--"] else command
        if not command:
            raise SecretValidationError()
        execute(args.provider, command, args.secret_root)
    except SecretValidationError:
        print(FAILURE, file=sys.stderr)
        return 78
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
