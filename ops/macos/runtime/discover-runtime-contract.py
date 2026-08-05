#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any


IGNORED_DIRECTORIES = {
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

TEST_DIRECTORY_NAMES = {
    "test",
    "tests",
}

DEPENDENCY_SCORES = {
    "pyproject.toml": 100,
    "requirements.txt": 95,
    "requirements-prod.txt": 94,
    "requirements-production.txt": 94,
    "requirements/base.txt": 85,
    "requirements/production.txt": 94,
}

ENVIRONMENT_PATTERN = re.compile(
    r"""
    (?:
        os\.getenv
        |
        os\.environ\.get
        |
        os\.environ
    )
    \s*
    [\(\[]
    \s*
    ["']
    ([A-Z][A-Z0-9_]*)
    ["']
    """,
    re.VERBOSE,
)

CANONICAL_RUNTIME_LAUNCHERS = (
    "ops/macos/launchd/run-shadow-api.sh",
    "ops/macos/launchd/run-shadow-daemon.sh",
)

UVICORN_TARGET_PATTERN = re.compile(
    r"(?:^|\s)-m(?:[ \t]|\\\r?\n)+uvicorn"
    r"(?:[ \t]|\\\r?\n)+([^\s\\]+)",
    re.MULTILINE,
)

FULL_RUNTIME_TARGET_PATTERN = re.compile(
    r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+:[A-Za-z_]\w*\Z"
)

HTTP_PATH_PATTERN = re.compile(r"/(?!/)[^\s?#]*\Z")


def run_command(
    arguments: list[str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def run_git(
    root: Path,
    *arguments: str,
) -> str:
    result = run_command(
        [
            "git",
            "-C",
            str(root),
            *arguments,
        ]
    )

    return result.stdout.strip()


def command_info(command: str) -> dict[str, str]:
    path = shutil.which(command)

    if path is None:
        return {
            "path": "",
            "version": "",
        }

    result = run_command(
        [
            path,
            "--version",
        ]
    )

    output = (
        result.stdout.strip()
        or result.stderr.strip()
    )

    return {
        "path": path,
        "version": (
            output.splitlines()[0]
            if output
            else ""
        ),
    }


def is_test_file(
    root: Path,
    path: Path,
) -> bool:
    relative = path.relative_to(root)

    if any(
        part.lower() in TEST_DIRECTORY_NAMES
        for part in relative.parts
    ):
        return True

    filename = path.name.lower()

    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
    )


def module_name(
    root: Path,
    path: Path,
) -> str:
    relative = path.relative_to(root)
    parts = list(relative.with_suffix("").parts)

    if parts and parts[0] == "src":
        parts = parts[1:]

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def function_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return node.attr

    return ""


def assigned_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Assign):
        names = []

        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)

        return names

    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            return [node.target.id]

    return []


def assigned_value(node: ast.AST) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.value

    if isinstance(node, ast.AnnAssign):
        return node.value

    return None


def dependency_score(
    root: Path,
    path: Path,
) -> int:
    relative = str(path.relative_to(root))
    filename = path.name.lower()

    if relative in DEPENDENCY_SCORES:
        return DEPENDENCY_SCORES[relative]

    if filename == "pyproject.toml":
        return 90

    if (
        filename.startswith("requirements")
        and filename.endswith(".txt")
    ):
        score = 70

        lowered = relative.lower()

        if "prod" in lowered:
            score += 15

        if "base" in lowered:
            score += 5

        return score

    return 0


def dependency_install_command(
    root: Path,
    path: Path,
) -> str:
    relative = str(path.relative_to(root))

    if path.name == "pyproject.toml":
        return "python -m pip install ."

    if (
        path.name.lower().startswith("requirements")
        and path.suffix == ".txt"
    ):
        return (
            "python -m pip install -r "
            + relative
        )

    return ""


def discover_dependency_files(
    root: Path,
    files: list[Path],
) -> dict[str, Any]:
    candidates = []

    for path in files:
        score = dependency_score(
            root,
            path,
        )

        if score <= 0:
            continue

        candidates.append(
            {
                "path": str(path.relative_to(root)),
                "score": score,
                "install_command":
                    dependency_install_command(
                        root,
                        path,
                    ),
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["path"],
        )
    )

    selected = None
    ambiguous = False

    if candidates:
        top_score = candidates[0]["score"]

        top_candidates = [
            item
            for item in candidates
            if item["score"] == top_score
        ]

        if len(top_candidates) == 1:
            selected = top_candidates[0]
        else:
            ambiguous = True

    return {
        "candidates": candidates,
        "selected": selected,
        "ambiguous": ambiguous,
    }


def discover_python_contract(
    root: Path,
    python_files: list[Path],
) -> dict[str, Any]:
    application_objects: list[dict[str, str]] = []
    explicit_uvicorn_targets: set[str] = set()
    health_endpoints: set[tuple[str, str, str]] = set()
    environment_variables: set[str] = set()
    main_guard_files: set[str] = set()
    framework_files: dict[str, set[str]] = {
        "fastapi": set(),
        "flask": set(),
        "uvicorn": set(),
    }

    for path in python_files:
        if is_test_file(root, path):
            continue

        relative = str(path.relative_to(root))

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            continue

        environment_variables.update(
            ENVIRONMENT_PATTERN.findall(source)
        )

        if 'if __name__ == "__main__"' in source:
            main_guard_files.add(relative)

        try:
            tree = ast.parse(
                source,
                filename=str(path),
            )
        except SyntaxError:
            continue

        module = module_name(
            root,
            path,
        )

        for node in ast.walk(tree):
            value = assigned_value(node)

            if (
                value is not None
                and isinstance(value, ast.Call)
            ):
                constructor = function_name(
                    value.func
                )

                if constructor in {
                    "FastAPI",
                    "Flask",
                }:
                    framework = (
                        "fastapi"
                        if constructor == "FastAPI"
                        else "flask"
                    )

                    framework_files[
                        framework
                    ].add(relative)

                    for name in assigned_names(node):
                        application_objects.append(
                            {
                                "framework": framework,
                                "file": relative,
                                "module": module,
                                "variable": name,
                                "target": (
                                    f"{module}:{name}"
                                    if module
                                    else name
                                ),
                            }
                        )

            if not isinstance(node, ast.Call):
                continue

            called_name = function_name(
                node.func
            )

            if called_name == "run":
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(
                        node.func.value,
                        ast.Name,
                    )
                    and node.func.value.id == "uvicorn"
                ):
                    framework_files[
                        "uvicorn"
                    ].add(relative)

                    if node.args:
                        first_argument = node.args[0]

                        if (
                            isinstance(
                                first_argument,
                                ast.Constant,
                            )
                            and isinstance(
                                first_argument.value,
                                str,
                            )
                        ):
                            explicit_uvicorn_targets.add(
                                first_argument.value
                            )

            if not isinstance(
                node.func,
                ast.Attribute,
            ):
                continue

            method = node.func.attr

            if method not in {
                "get",
                "route",
                "api_route",
            }:
                continue

            if not node.args:
                continue

            first_argument = node.args[0]

            if not (
                isinstance(
                    first_argument,
                    ast.Constant,
                )
                and isinstance(
                    first_argument.value,
                    str,
                )
            ):
                continue

            endpoint = first_argument.value

            if HTTP_PATH_PATTERN.fullmatch(endpoint) is None:
                continue

            endpoint_lower = endpoint.lower()

            if not any(
                marker in endpoint_lower
                for marker in (
                    "health",
                    "ready",
                    "live",
                    "status",
                )
            ):
                continue

            health_endpoints.add(
                (
                    relative,
                    method.upper(),
                    endpoint,
                )
            )

    inferred_targets = {
        item["target"]
        for item in application_objects
        if item["framework"] == "fastapi"
    }

    inferred_runtime_targets = sorted(
        explicit_uvicorn_targets | inferred_targets
    )

    health_endpoint_output = [
        {
            "file": file,
            "method": method,
            "path": endpoint,
        }
        for file, method, endpoint in health_endpoints
    ]

    framework_output = {
        framework: sorted(paths)
        for framework, paths
        in framework_files.items()
        if paths
    }

    return {
        "application_objects": sorted(
            application_objects,
            key=lambda item: (
                item["target"],
                item["file"],
            ),
        ),
        "inferred_runtime_targets": inferred_runtime_targets,
        "health_endpoints": sorted(
            health_endpoint_output,
            key=lambda item: (
                item["path"],
                item["file"],
                item["method"],
            ),
        ),
        "framework_files": framework_output,
        "environment_variable_names": sorted(
            environment_variables
        ),
        "main_guard_files": sorted(
            main_guard_files
        ),
    }


def discover_launcher_contract(root: Path) -> dict[str, Any]:
    launchers: list[dict[str, Any]] = []

    for relative in CANONICAL_RUNTIME_LAUNCHERS:
        path = root / relative
        targets: list[str] = []
        error = ""

        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            error = "launcher_unavailable"
        else:
            targets = UVICORN_TARGET_PATTERN.findall(source)

            if not targets:
                error = "launcher_target_missing"
            elif len(targets) != 1:
                error = "launcher_target_multiple"
            elif FULL_RUNTIME_TARGET_PATTERN.fullmatch(targets[0]) is None:
                error = "launcher_target_malformed"

        launchers.append(
            {
                "path": relative,
                "targets": targets,
                "valid": not error,
                "error": error,
            }
        )

    valid_targets = [
        launcher["targets"][0]
        for launcher in launchers
        if launcher["valid"]
    ]
    all_valid = all(launcher["valid"] for launcher in launchers)
    agreed = (
        all_valid
        and len(valid_targets) == len(CANONICAL_RUNTIME_LAUNCHERS)
        and len(set(valid_targets)) == 1
    )
    selected_target = valid_targets[0] if agreed else None

    return {
        "canonical_launchers": launchers,
        "targets": sorted(set(valid_targets)),
        "all_valid": all_valid,
        "agreed": agreed,
        "selected_runtime_target": selected_target,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        required=True,
        help="AIControlCenter repository root",
    )

    arguments = parser.parse_args()

    root = Path(
        arguments.root
    ).expanduser().resolve()

    if not (root / ".git").is_dir():
        raise SystemExit(
            f"Git repository not found: {root}"
        )

    files: list[Path] = []

    for current_root, directories, filenames in os.walk(
        root
    ):
        directories[:] = [
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        ]

        current = Path(current_root)

        for filename in filenames:
            files.append(
                current / filename
            )

    python_files = [
        path
        for path in files
        if path.suffix == ".py"
    ]

    test_files = [
        str(path.relative_to(root))
        for path in python_files
        if is_test_file(
            root,
            path,
        )
    ]

    dependency = discover_dependency_files(
        root,
        files,
    )

    python_contract = discover_python_contract(
        root,
        python_files,
    )
    launcher_contract = discover_launcher_contract(root)

    dirty_lines = [
        line
        for line in run_git(
            root,
            "status",
            "--porcelain",
        ).splitlines()
        if line
    ]

    selected_dependency = dependency["selected"]
    runtime_targets = launcher_contract["targets"]
    health_endpoints = python_contract[
        "health_endpoints"
    ]

    selected_runtime_target = launcher_contract[
        "selected_runtime_target"
    ]

    runtime_command = ""

    if selected_runtime_target is not None:
        runtime_command = (
            "python -m uvicorn "
            f"{selected_runtime_target} "
            "--host 127.0.0.1 "
            "--port 8000"
        )

    test_command = (
        "python -m pytest -q"
        if test_files
        else ""
    )

    python_312 = command_info(
        "python3.12"
    )

    checks = {
        "python_3_12_available":
            bool(python_312["path"]),
        "repository_clean":
            len(dirty_lines) == 0,
        "dependency_selected":
            selected_dependency is not None,
        "dependency_unambiguous":
            not dependency["ambiguous"],
        "runtime_target_selected":
            selected_runtime_target is not None,
        "runtime_target_unambiguous":
            launcher_contract["agreed"],
        "health_endpoint_found":
            len(health_endpoints) > 0,
        "tests_found":
            len(test_files) > 0,
    }

    gate_passed = all(
        checks.values()
    )

    output: dict[str, Any] = {
        "schema_version": "1.0",
        "runtime_contract_gate_passed":
            gate_passed,
        "checks": checks,
        "repository": {
            "path": str(root),
            "branch": run_git(
                root,
                "branch",
                "--show-current",
            ),
            "commit": run_git(
                root,
                "rev-parse",
                "HEAD",
            ),
            "remote": run_git(
                root,
                "remote",
                "get-url",
                "origin",
            ),
            "dirty_file_count":
                len(dirty_lines),
        },
        "python": {
            "python_3_12": python_312,
            "python_file_count":
                len(python_files),
        },
        "dependency": dependency,
        "application": {
            **python_contract,
            "launcher_contract": launcher_contract,
            "runtime_targets": runtime_targets,
            "runtime_target_ambiguous":
                not launcher_contract["agreed"],
            "selected_runtime_target":
                selected_runtime_target,
            "recommended_runtime_command":
                runtime_command,
        },
        "tests": {
            "file_count": len(test_files),
            "files": sorted(test_files),
            "recommended_command":
                test_command,
        },
        "production_candidate": {
            "dependency_file": (
                selected_dependency["path"]
                if selected_dependency
                else None
            ),
            "install_command": (
                selected_dependency[
                    "install_command"
                ]
                if selected_dependency
                else None
            ),
            "runtime_target":
                selected_runtime_target,
            "runtime_command":
                runtime_command,
            "health_endpoints":
                health_endpoints,
            "test_command":
                test_command,
        },
        "safety": {
            "read_only": True,
            "secret_values_read": False,
            "dependencies_installed": False,
            "processes_started": False,
            "files_modified": False,
        },
    }

    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
