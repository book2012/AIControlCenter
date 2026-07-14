#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import tempfile
from typing import Any


DEFAULT_INPUT = Path(
    "/var/log/aicontrolcenter/"
    "shadow-observation.jsonl"
)


def parse_timestamp(
    value: Any,
) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return None


def load_records(
    path: Path,
) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    invalid_lines = 0

    if not path.is_file():
        return records, invalid_lines

    with path.open(
        "r",
        encoding="utf-8",
    ) as source:
        for line in source:
            value = line.strip()

            if not value:
                continue

            try:
                payload = json.loads(value)
            except json.JSONDecodeError:
                invalid_lines += 1
                continue

            if not isinstance(payload, dict):
                invalid_lines += 1
                continue

            records.append(payload)

    return records, invalid_lines


def numeric_values(
    records: list[dict[str, Any]],
    section: str,
    field: str,
) -> list[float]:
    values: list[float] = []

    for record in records:
        container = record.get(section)

        if not isinstance(container, dict):
            continue

        value = container.get(field)

        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            values.append(float(value))

    return values


def integer_values(
    records: list[dict[str, Any]],
    section: str,
    field: str,
) -> list[int]:
    values: list[int] = []

    for record in records:
        container = record.get(section)

        if not isinstance(container, dict):
            continue

        value = container.get(field)

        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            values.append(value)

    return values


def check_value(
    record: dict[str, Any],
    name: str,
) -> bool:
    checks = record.get("checks")

    if not isinstance(checks, dict):
        return False

    return checks.get(name) is True


def atomic_write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        json.dump(
            payload,
            temporary,
            indent=2,
            ensure_ascii=False,
        )

        temporary.write("\n")
        temporary.flush()

        temporary_path = Path(
            temporary.name
        )

    temporary_path.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize AIControlCenter "
            "Shadow observation JSON Lines"
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    arguments = parser.parse_args()

    records, invalid_lines = load_records(
        arguments.input
    )

    timestamp_pairs = [
        (
            timestamp,
            record,
        )
        for record in records
        if (
            timestamp := parse_timestamp(
                record.get("generated_at")
            )
        )
        is not None
    ]

    timestamp_pairs.sort(
        key=lambda item: item[0]
    )

    ordered_records = [
        record
        for _, record in timestamp_pairs
    ]

    timestamps = [
        timestamp
        for timestamp, _ in timestamp_pairs
    ]

    first_time = (
        timestamps[0]
        if timestamps
        else None
    )

    last_time = (
        timestamps[-1]
        if timestamps
        else None
    )

    duration_hours = (
        (
            last_time - first_time
        ).total_seconds()
        / 3600
        if first_time is not None
        and last_time is not None
        else 0.0
    )

    sample_count = len(records)

    passed_count = sum(
        record.get(
            "observation_gate_passed"
        )
        is True
        for record in records
    )

    failed_count = (
        sample_count - passed_count
    )

    success_ratio = (
        passed_count / sample_count
        if sample_count
        else 0.0
    )

    pids = integer_values(
        ordered_records,
        "process",
        "pid",
    )

    pid_transitions = sum(
        left != right
        for left, right in zip(
            pids,
            pids[1:],
        )
    )

    cpu_values = numeric_values(
        ordered_records,
        "process",
        "cpu_percent",
    )

    rss_values = integer_values(
        ordered_records,
        "process",
        "rss_kb",
    )

    stdout_sizes = integer_values(
        ordered_records,
        "logs",
        "stdout_bytes",
    )

    stderr_sizes = integer_values(
        ordered_records,
        "logs",
        "stderr_bytes",
    )

    critical_violations = sum(
        not (
            check_value(
                record,
                "listener_local_only",
            )
            and
            check_value(
                record,
                "process_user_non_root",
            )
        )
        for record in records
    )

    final_sample_passed = (
        bool(ordered_records)
        and
        ordered_records[-1].get(
            "observation_gate_passed"
        )
        is True
    )

    minimum_window_reached = (
        duration_hours >= 23.5
    )

    minimum_samples_reached = (
        sample_count >= 276
    )

    success_ratio_acceptable = (
        success_ratio >= 0.995
    )

    no_invalid_lines = (
        invalid_lines == 0
    )

    no_critical_violations = (
        critical_violations == 0
    )

    observation_complete = (
        minimum_window_reached
        and
        minimum_samples_reached
    )

    gate_passed = all(
        (
            observation_complete,
            success_ratio_acceptable,
            no_invalid_lines,
            no_critical_violations,
            final_sample_passed,
        )
    )

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "shadow_observation_gate_passed":
            gate_passed,
        "observation_complete":
            observation_complete,
        "source": str(arguments.input),
        "window": {
            "first_sample": (
                first_time.isoformat()
                if first_time
                else ""
            ),
            "last_sample": (
                last_time.isoformat()
                if last_time
                else ""
            ),
            "duration_hours":
                round(duration_hours, 3),
        },
        "samples": {
            "total": sample_count,
            "timestamped":
                len(ordered_records),
            "passed": passed_count,
            "failed": failed_count,
            "invalid_lines": invalid_lines,
            "success_ratio":
                round(success_ratio, 6),
            "required_minimum": 276,
        },
        "process": {
            "unique_pids":
                sorted(set(pids)),
            "pid_transitions":
                pid_transitions,
            "max_cpu_percent": (
                max(cpu_values)
                if cpu_values
                else None
            ),
            "max_rss_kb": (
                max(rss_values)
                if rss_values
                else None
            ),
        },
        "logs": {
            "stdout_growth_bytes": (
                stdout_sizes[-1]
                - stdout_sizes[0]
                if len(stdout_sizes) >= 2
                else 0
            ),
            "stderr_growth_bytes": (
                stderr_sizes[-1]
                - stderr_sizes[0]
                if len(stderr_sizes) >= 2
                else 0
            ),
        },
        "checks": {
            "minimum_window_reached":
                minimum_window_reached,
            "minimum_samples_reached":
                minimum_samples_reached,
            "success_ratio_acceptable":
                success_ratio_acceptable,
            "no_invalid_lines":
                no_invalid_lines,
            "no_critical_violations":
                no_critical_violations,
            "final_sample_passed":
                final_sample_passed,
        },
    }

    atomic_write_json(
        arguments.output,
        report,
    )

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
