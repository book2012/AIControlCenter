#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import plistlib
import subprocess
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[1]
)
ADAPTER_CONFIG_PATH = (
    REPOSITORY_ROOT
    / "config/"
    "governance_scheduler_smappservice.json"
)


class BuildError(RuntimeError):
    pass


def checked(
    arguments: list[str],
) -> str:
    completed = subprocess.run(
        arguments,
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        detail = (
            completed.stderr.strip()
            or completed.stdout.strip()
        )
        raise BuildError(
            f"{' '.join(arguments)}: {detail}"
        )

    return completed.stdout.strip()


def resolve_swift_toolchain() -> dict[str, str]:
    sdk_path = checked(
        [
            "/usr/bin/xcrun",
            "--sdk",
            "macosx",
            "--show-sdk-path",
        ]
    )
    sdk_version = checked(
        [
            "/usr/bin/xcrun",
            "--sdk",
            "macosx",
            "--show-sdk-version",
        ]
    )
    architecture = platform.machine()

    if architecture not in {
        "arm64",
        "x86_64",
    }:
        raise BuildError(
            "unsupported architecture: "
            + architecture
        )

    return {
        "architecture": architecture,
        "sdk_path": sdk_path,
        "sdk_version": sdk_version,
        "target": (
            f"{architecture}-"
            "apple-macosx13.0"
        ),
    }


def swift_compile(
    *,
    source: Path,
    destination: Path,
    frameworks: list[str],
    toolchain: dict[str, str],
) -> None:
    arguments = [
        "/usr/bin/xcrun",
        "--sdk",
        "macosx",
        "swiftc",
        "-sdk",
        toolchain["sdk_path"],
        "-target",
        toolchain["target"],
        "-O",
    ]

    for framework in frameworks:
        arguments.extend(
            [
                "-framework",
                framework,
            ]
        )

    arguments.extend(
        [
            str(source),
            "-o",
            str(destination),
        ]
    )

    checked(arguments)


def build_agent_document(
    *,
    definition: dict[str, Any],
    repository_root: Path,
    runner_executable: str,
    log_directory: Path,
) -> dict[str, Any]:
    label = definition["label"]
    operation = definition["operation"]

    return {
        "BundleProgram": (
            "Contents/Resources/"
            + runner_executable
        ),
        "EnvironmentVariables": {
            "AICONTROLCENTER_REPOSITORY": (
                str(repository_root.resolve())
            ),
            "HOME": str(Path.home()),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        "KeepAlive": False,
        "Label": label,
        "ProgramArguments": [
            runner_executable,
            "--operation",
            operation,
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
    }


def write_plist(
    path: Path,
    document: dict[str, Any],
) -> None:
    path.write_bytes(
        plistlib.dumps(
            document,
            fmt=plistlib.FMT_XML,
            sort_keys=True,
        )
    )


def build_bundle(
    output_directory: Path,
) -> dict[str, Any]:
    adapter = json.loads(
        ADAPTER_CONFIG_PATH.read_text(
            encoding="utf-8"
        )
    )
    cadence_path = (
        REPOSITORY_ROOT
        / adapter["cadence_policy"]
    )
    cadence = json.loads(
        cadence_path.read_text(
            encoding="utf-8"
        )
    )
    definitions = cadence.get(
        "definitions",
        [],
    )
    bundle = adapter["bundle"]

    if len(definitions) != 2:
        raise BuildError(
            "exactly two cadence definitions "
            "are required"
        )

    app = (
        output_directory.resolve()
        / bundle["name"]
    )

    if app.exists():
        raise BuildError(
            f"bundle already exists: {app}"
        )

    macos_directory = (
        app / "Contents/MacOS"
    )
    resources_directory = (
        app / "Contents/Resources"
    )
    agents_directory = (
        app
        / "Contents/Library/LaunchAgents"
    )

    for directory in (
        macos_directory,
        resources_directory,
        agents_directory,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    toolchain = resolve_swift_toolchain()

    registrar = (
        macos_directory
        / bundle[
            "registrar_executable"
        ]
    )
    runner = (
        resources_directory
        / bundle["runner_executable"]
    )

    swift_compile(
        source=(
            REPOSITORY_ROOT
            / "macos/"
            "governance_scheduler/"
            "Registrar.swift"
        ),
        destination=registrar,
        frameworks=[
            "Foundation",
            "ServiceManagement",
        ],
        toolchain=toolchain,
    )
    swift_compile(
        source=(
            REPOSITORY_ROOT
            / "macos/"
            "governance_scheduler/"
            "Runner.swift"
        ),
        destination=runner,
        frameworks=[
            "Foundation",
        ],
        toolchain=toolchain,
    )

    os.chmod(registrar, 0o755)
    os.chmod(runner, 0o755)

    write_plist(
        app / "Contents/Info.plist",
        {
            "CFBundleDevelopmentRegion": "en",
            "CFBundleExecutable": (
                bundle[
                    "registrar_executable"
                ]
            ),
            "CFBundleIdentifier": (
                bundle["identifier"]
            ),
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleName": (
                "AIControlCenter Scheduler"
            ),
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1",
            "LSBackgroundOnly": True,
            "LSMinimumSystemVersion": "13.0",
        },
    )

    log_directory = (
        Path.home()
        / "Library/Logs/"
        "AIControlCenter/governance"
    )
    agent_paths: list[Path] = []

    for definition in definitions:
        document = build_agent_document(
            definition=definition,
            repository_root=(
                REPOSITORY_ROOT
            ),
            runner_executable=(
                bundle[
                    "runner_executable"
                ]
            ),
            log_directory=log_directory,
        )
        path = (
            agents_directory
            / (
                definition["label"]
                + ".plist"
            )
        )
        write_plist(path, document)
        agent_paths.append(path)

    for executable in (
        registrar,
        runner,
    ):
        checked(
            [
                "/usr/bin/codesign",
                "--force",
                "--sign",
                "-",
                str(executable),
            ]
        )

    checked(
        [
            "/usr/bin/codesign",
            "--force",
            "--deep",
            "--sign",
            "-",
            str(app),
        ]
    )
    checked(
        [
            "/usr/bin/codesign",
            "--verify",
            "--deep",
            "--strict",
            str(app),
        ]
    )

    return {
        "agent_plists": [
            str(path)
            for path in agent_paths
        ],
        "app_bundle": str(app),
        "bundle_identifier": (
            bundle["identifier"]
        ),
        "production_registered": False,
        "result": "PASS",
        "signed": True,
        "swift_toolchain": toolchain,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--json",
        action="store_true",
    )
    arguments = parser.parse_args()

    result = build_bundle(
        arguments.output_dir
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as error:
        print(
            json.dumps(
                {
                    "error": str(error),
                    "result": "FAIL",
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        raise SystemExit(1)
