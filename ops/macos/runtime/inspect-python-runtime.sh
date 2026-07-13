#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="${AICONTROLCENTER_ROOT:-$HOME/AIControlCenter}"

if [[ ! -d "$ROOT/.git" ]]; then
    echo "[ERROR] Git repository not found: $ROOT" >&2
    exit 1
fi

python3 - "$ROOT" <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
import re
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

runtime_names = {
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
    "fastapi": (
        "from fastapi",
        "import fastapi",
        "FastAPI(",
    ),
    "flask": (
        "from flask",
        "import flask",
        "Flask(",
    ),
    "django": (
        "DJANGO_SETTINGS_MODULE",
        "from django",
        "import django",
    ),
    "uvicorn": (
        "uvicorn.run",
        "import uvicorn",
        "from uvicorn",
    ),
    "gunicorn": (
        "gunicorn",
    ),
    "typer": (
        "Typer(",
        "import typer",
        "from typer",
    ),
    "click": (
        "@click.",
        "import click",
        "from click",
    ),
    "celery": (
        "Celery(",
        "import celery",
        "from celery",
    ),
    "pytest": (
        "import pytest",
        "from pytest",
    ),
}

environment_patterns = (
    re.compile(
        r"""os\.getenv\(\s*["']([A-Z][A-Z0-9_]*)["']"""
    ),
    re.compile(
        r"""os\.environ\.get\(\s*["']([A-Z][A-Z0-9_]*)["']"""
    ),
    re.compile(
        r"""os\.environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]"""
    ),
)


def relative(path: Path) -> str:
    return str(path.relative_to(root))


def run_git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
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

for current_root, directories, filenames in os.walk(root):
    directories[:] = [
        directory
        for directory in directories
        if directory not in ignored_directories
    ]

    current_path = Path(current_root)

    for filename in filenames:
        all_files.append(current_path / filename)

dependency_files: list[str] = []
candidate_entrypoints: list[str] = []
runtime_files: list[str] = []
launchd_files: list[str] = []
shell_scripts: list[str] = []
test_files: list[str] = []
python_files: list[Path] = []

for path in all_files:
    filename = path.name
    filename_lower = filename.lower()
    relative_path = relative(path)

    if (
        filename in dependency_names
        or (
            filename_lower.startswith("requirements")
            and filename_lower.endswith(".txt")
        )
    ):
        dependency_files.append(relative_path)

    if filename in entrypoint_names:
        candidate_entrypoints.append(relative_path)

    if (
        filename in runtime_names
        or filename_lower.startswith("docker-compose")
        or filename_lower.startswith("compose.")
    ):
        runtime_files.append(relative_path)

    if path.suffix == ".plist":
        launchd_files.append(relative_path)

    if path.suffix == ".sh":
        shell_scripts.append(relative_path)

    if path.suffix == ".py":
        python_files.append(path)

        path_parts = {
            part.lower()
            for part in path.relative_to(root).parts
        }

        if (
            "tests" in path_parts
            or filename_lower.startswith("test_")
            or filename_lower.endswith("_test.py")
        ):
            test_files.append(relative_path)

framework_indicators: dict[str, list[str]] = {
    framework: []
    for framework in framework_patterns
}

main_guard_files: list[str] = []
health_indicator_files: list[str] = []
environment_variable_names: set[str] = set()
uvicorn_targets: set[str] = set()

uvicorn_target_pattern = re.compile(
    r"""uvicorn\.run\(\s*["']([^"']+)["']"""
)

for path in python_files:
    try:
        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )[:524288]
    except OSError:
        continue

    relative_path = relative(path)
    content_lower = content.lower()

    if 'if __name__ == "__main__"' in content:
        main_guard_files.append(relative_path)

    if (
        "/health" in content_lower
        or "health_check" in content_lower
        or "healthcheck" in content_lower
        or "health status" in content_lower
        or "readiness" in content_lower
        or "liveness" in content_lower
    ):
        health_indicator_files.append(relative_path)

    for framework, patterns in framework_patterns.items():
        if any(
            pattern.lower() in content_lower
            for pattern in patterns
        ):
            framework_indicators[framework].append(relative_path)

    for pattern in environment_patterns:
        environment_variable_names.update(
            pattern.findall(content)
        )

    uvicorn_targets.update(
        uvicorn_target_pattern.findall(content)
    )

framework_indicators = {
    framework: sorted(set(paths))
    for framework, paths in framework_indicators.items()
    if paths
}

dirty_files = [
    line
    for line in run_git(
        "status",
        "--porcelain",
    ).splitlines()
    if line
]

result: dict[str, Any] = {
    "schema_version": "1.0",
    "repository": {
        "path": str(root),
        "branch": run_git(
            "branch",
            "--show-current",
        ),
        "commit": run_git(
            "rev-parse",
            "HEAD",
        ),
        "remote": run_git(
            "remote",
            "get-url",
            "origin",
        ),
        "dirty_file_count": len(dirty_files),
    },
    "python": {
        "python3": command_info("python3"),
        "python3_12": command_info("python3.12"),
        "python_file_count": len(python_files),
        "dependency_files": sorted(
            set(dependency_files)
        ),
        "candidate_entrypoints": sorted(
            set(candidate_entrypoints)
        ),
        "main_guard_files": sorted(
            set(main_guard_files)
        ),
        "framework_indicators": framework_indicators,
        "health_indicator_files": sorted(
            set(health_indicator_files)
        ),
        "uvicorn_targets": sorted(
            uvicorn_targets
        ),
        "environment_variable_names": sorted(
            environment_variable_names
        ),
        "test_file_count": len(test_files),
        "test_files": sorted(
            set(test_files)
        )[:200],
    },
    "runtime": {
        "configuration_files": sorted(
            set(runtime_files)
        ),
        "launchd_files": sorted(
            set(launchd_files)
        ),
        "shell_scripts": sorted(
            set(shell_scripts)
        ),
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
