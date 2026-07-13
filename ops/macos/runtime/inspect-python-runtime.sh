#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"

if [[ ! -d "$ROOT/.git" ]]; then
    echo "[ERROR] AIControlCenter Git repository not found: $ROOT" >&2
    exit 1
fi

python3 - "$ROOT" <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


root = Path(sys.argv[1]).expanduser().resolve()

ignored_directories = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "dist",
    "build",
    "vendor",
}

dependency_names = {
    "pyproject.toml",
    "poetry.lock",
    "pdm.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "environment.yml",
    "environment.yaml",
}

entrypoint_names = {
    "__main__.py",
    "main.py",
    "app.py",
    "api.py",
    "server.py",
    "run.py",
    "manage.py",
    "cli.py",
    "wsgi.py",
    "asgi.py",
    "worker.py",
}

runtime_config_names = {
    "Dockerfile",
    "Procfile",
    "Makefile",
    "Taskfile.yml",
    "Taskfile.yaml",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}

framework_patterns = {
    "fastapi": "FastAPI(",
    "flask": "Flask(",
    "django": "DJANGO_SETTINGS_MODULE",
    "uvicorn": "uvicorn",
    "gunicorn": "gunicorn",
    "typer": "Typer(",
    "click": "@click.",
    "celery": "Celery(",
    "pytest": "pytest",
}


def relative(path: Path) -> str:
    return str(path.relative_to(root))


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def command_info(command: str) -> dict[str, str]:
    executable = shutil.which(command)

    if executable is None:
        return {
            "path": "",
            "version": "",
        }

    result = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
    )

    output = result.stdout.strip() or result.stderr.strip()
    first_line = output.splitlines()[0] if output else ""

    return {
        "path": executable,
        "version": first_line,
    }


all_files: list[Path] = []

for current_root, directories, files in os.walk(root):
    directories[:] = [
        directory
        for directory in directories
        if directory not in ignored_directories
    ]

    current = Path(current_root)

    for filename in files:
        all_files.append(current / filename)

dependency_files: list[str] = []
entrypoints: list[str] = []
runtime_configs: list[str] = []
test_files: list[str] = []
launchd_files: list[str] = []
shell_scripts: list[str] = []
python_files: list[Path] = []

for path in all_files:
    name = path.name
    lower_name = name.lower()
    rel = relative(path)

    if (
        name in dependency_names
        or (
            lower_name.startswith("requirements")
            and lower_name.endswith(".txt")
        )
    ):
        dependency_files.append(rel)

    if name in entrypoint_names:
        entrypoints.append(rel)

    if (
        name in runtime_config_names
        or lower_name.startswith("docker-compose")
        or lower_name.startswith("compose.")
    ):
        runtime_configs.append(rel)

    if path.suffix == ".plist":
        launchd_files.append(rel)

    if path.suffix == ".sh":
        shell_scripts.append(rel)

    if path.suffix == ".py":
        python_files.append(path)

        parts = {
            part.lower()
            for part in path.relative_to(root).parts
        }

        if (
            "tests" in parts
            or lower_name.startswith("test_")
            or lower_name.endswith("_test.py")
        ):
            test_files.append(rel)

framework_indicators: dict[str, list[str]] = {
    key: []
    for key in framework_patterns
}

main_guard_files: list[str] = []
health_indicator_files: list[str] = []

for path in python_files:
    try:
        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )[:262144]
    except OSError:
        continue

    rel = relative(path)

    if 'if __name__ == "__main__"' in content:
        main_guard_files.append(rel)

    lowered = content.lower()

    if (
        "/health" in lowered
        or "health_check" in lowered
        or "healthcheck" in lowered
        or "health status" in lowered
    ):
        health_indicator_files.append(rel)

    for framework, pattern in framework_patterns.items():
        if pattern.lower() in lowered:
            framework_indicators[framework].append(rel)

framework_indicators = {
    key: sorted(set(value))
    for key, value in framework_indicators.items()
    if value
}

root_directories = sorted(
    path.name
    for path in root.iterdir()
    if path.is_dir()
    and path.name not in ignored_directories
)

dirty_lines = [
    line
    for line in run_git("status", "--porcelain").splitlines()
    if line
]

result: dict[str, Any] = {
    "schema_version": "1.0",
    "repository": {
        "path": str(root),
        "branch": run_git("branch", "--show-current"),
        "commit": run_git("rev-parse", "HEAD"),
        "remote": run_git("remote", "get-url", "origin"),
        "dirty_file_count": len(dirty_lines),
        "root_directories": root_directories,
    },
    "python": {
        "python3": command_info("python3"),
        "python3_12": command_info("python3.12"),
        "python_file_count": len(python_files),
        "dependency_files": sorted(set(dependency_files)),
        "candidate_entrypoints": sorted(set(entrypoints)),
        "main_guard_files": sorted(set(main_guard_files)),
        "framework_indicators": framework_indicators,
        "health_indicator_files": sorted(
            set(health_indicator_files)
        ),
        "test_file_count": len(test_files),
        "test_files": sorted(set(test_files))[:100],
    },
    "runtime": {
        "configuration_files": sorted(set(runtime_configs)),
        "launchd_files": sorted(set(launchd_files)),
        "shell_scripts": sorted(set(shell_scripts)),
    },
    "safety": {
        "read_only": True,
        "secret_values_read": False,
        "processes_started": False,
        "files_modified": False,
    },
}

print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    )
)
PY
