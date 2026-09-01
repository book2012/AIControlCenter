#!/usr/bin/env python3
"""Finalize durable evidence for the canonical deployment regression gate."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
from typing import Sequence

SCHEMA_VERSION = "ops-val-01b/canonical-evidence/v2"
CANONICAL_ENTRYPOINT = "ops/macos/validation/run-deployment-regression-gate.sh"
EVIDENCE_PARENT = Path("/private/tmp")
EVIDENCE_PREFIX = "aicontrolcenter-canonical-evidence."

_OUTCOME = (
    r"\d+ (?:passed|failed|errors?|skipped|deselected|xfailed|xpassed|warnings?"
    r"|subtests? passed)"
)
_SUMMARY = re.compile(
    rf"^(?:=+ )?({_OUTCOME}(?:, {_OUTCOME})* in "
    r"\d+(?:\.\d+)?s(?: \(\d+:\d{2}:\d{2}\))?)(?: =+)?$"
)
_FAILURE_OUTCOME = re.compile(
    r"(?:^|, )\d+ (?:failed|errors?)(?=, | in )"
)
_POSITIVE_PASS_OUTCOME = re.compile(
    r"(?:^|, )[1-9]\d* (?:passed|subtests? passed)(?=, | in )"
)
_INVOCATION_ID = re.compile(r"^[0-9a-f]{32}$")


def exact_final_pytest_summary(output: str) -> str | None:
    """Return only a pytest summary on the final non-empty output line."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    match = _SUMMARY.fullmatch(lines[-1])
    return match.group(1) if match else None


def canonical_command(arguments: Sequence[str]) -> str:
    """Render the sole canonical entry point and its literal arguments."""
    return shlex.join([CANONICAL_ENTRYPOINT, *arguments])


def _validated_evidence_directory(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    if resolved.parent != EVIDENCE_PARENT:
        raise ValueError("evidence directory must be directly under /private/tmp")
    if not resolved.name.startswith(EVIDENCE_PREFIX):
        raise ValueError("evidence directory has an invalid namespace")
    if resolved.stat().st_uid != os.getuid():
        raise ValueError("evidence directory must be owned by the current user")
    if resolved.stat().st_mode & 0o777 != 0o700:
        raise ValueError("evidence directory mode must be 0700")
    return resolved


def _validated_invocation_id(invocation_id: str) -> str:
    if not _INVOCATION_ID.fullmatch(invocation_id):
        raise ValueError("invalid canonical invocation id")
    return invocation_id


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", text=True
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _evidence_state(
    pytest_exit_status: int,
    capture_exit_status: int,
    summary: str | None,
) -> str:
    if capture_exit_status != 0 or summary is None:
        return "CAPTURE_UNCERTAIN"
    if (
        pytest_exit_status == 0
        and _FAILURE_OUTCOME.search(summary) is None
        and _POSITIVE_PASS_OUTCOME.search(summary) is not None
    ):
        return "COMPLETED_PASS"
    return "COMPLETED_FAIL"


def finalize_evidence(
    evidence_directory: Path,
    pytest_exit_status: int,
    capture_exit_status: int,
    invocation_id: str,
    arguments: Sequence[str],
) -> dict[str, object]:
    """Atomically publish invocation-bound canonical evidence."""
    directory = _validated_evidence_directory(evidence_directory)
    validated_invocation_id = _validated_invocation_id(invocation_id)
    pytest_log = directory / "pytest.log"
    if not pytest_log.is_file():
        raise ValueError("pytest.log is missing")

    output = pytest_log.read_text(encoding="utf-8")
    summary = exact_final_pytest_summary(output)
    state = _evidence_state(
        pytest_exit_status,
        capture_exit_status,
        summary,
    )
    validated_pass = state == "COMPLETED_PASS"

    result: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "invocation_id": validated_invocation_id,
        "canonical_command": canonical_command(arguments),
        "state": state,
        "completed": state != "CAPTURE_UNCERTAIN",
        "capture_exit_status": capture_exit_status,
        "exit_status": pytest_exit_status,
        "pytest_summary": summary,
        "validated_pass": validated_pass,
    }

    _atomic_write(directory / "exit-status", f"{pytest_exit_status}\n")
    _atomic_write(
        directory / "result.json",
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_directory", type=Path)
    parser.add_argument("pytest_exit_status", type=int)
    parser.add_argument("capture_exit_status", type=int)
    parser.add_argument("invocation_id")
    parser.add_argument("canonical_arguments", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(argv)
    arguments = options.canonical_arguments
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]

    result = finalize_evidence(
        options.evidence_directory,
        options.pytest_exit_status,
        options.capture_exit_status,
        options.invocation_id,
        arguments,
    )

    if result["state"] == "CAPTURE_UNCERTAIN":
        print("Canonical evidence capture is uncertain", file=sys.stderr)
        return 4

    if options.pytest_exit_status == 0 and not result["validated_pass"]:
        print("Canonical evidence does not prove a passing run", file=sys.stderr)
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
