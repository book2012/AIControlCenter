"""JSON-first, read-only live preflight for SHOP-SERVICE-START-01B."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

Observer = Callable[[], object]


def _inspect_runtime() -> object:
    from ops.macos.shopping.runtime_inspector import inspect_runtime

    return inspect_runtime()


def _observe_storage_continuity() -> object:
    from ops.macos.shopping.storage_continuity_observer import observe_storage_continuity

    return observe_storage_continuity()


def _observe_runtime_cutover_source() -> object:
    from core.shopping.runtime_cutover_secret_source import observe_runtime_cutover_source

    return observe_runtime_cutover_source()


def _project(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    projection = getattr(value, "projection", None)
    if callable(projection):
        result = projection()
    else:
        to_json_safe = getattr(value, "to_json_safe", None)
        if not callable(to_json_safe):
            raise TypeError
        result = to_json_safe()
    if not isinstance(result, dict):
        raise TypeError
    return result


def _observe(observer: Observer, section: str) -> dict[str, object]:
    try:
        return _project(observer())
    except Exception:
        result: dict[str, object] = {
            "schema_version": "1.0",
            "inspection": "read-only",
            "available": False,
            "ready": False,
            "error_type": "ObserverFailure",
            "mutation_performed": False,
        }
        if section == "runtime_cutover_source":
            result["values_exposed"] = False
        return result


def collect_preflight(
    *,
    runtime_observer: Observer = _inspect_runtime,
    storage_observer: Observer = _observe_storage_continuity,
    source_observer: Observer = _observe_runtime_cutover_source,
) -> dict[str, object]:
    """Collect fixed-scope observations without creating operational authority."""
    return {
        "schema_version": "1.0",
        "authoritative_work_item": "SHOP-SERVICE-START-01B",
        "inspection": "read-only",
        "mutation_performed": False,
        "authorization_created": False,
        "authorization_consumed": False,
        "production_authority": False,
        "ubuntu_authority": False,
        "runtime": _observe(runtime_observer, "runtime"),
        "storage_continuity": _observe(storage_observer, "storage_continuity"),
        "runtime_cutover_source": _observe(source_observer, "runtime_cutover_source"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fixed SHOP-SERVICE-START-01B read-only preflight.",
    )
    parser.parse_args(argv)
    print(json.dumps(collect_preflight(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
