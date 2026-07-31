"""Optional test-root-confined JSON reporting."""

from pathlib import Path

from .models import TestOnlyAuthorizationSimulationError


def emit_json_report(result, *, root: Path, relative_name: str) -> Path:
    root = root.resolve()
    path = (root / relative_name).resolve()
    if root not in path.parents or path.suffix != ".json":
        raise TestOnlyAuthorizationSimulationError("REPORT_PATH_PROHIBITED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.canonical_json(), encoding="utf-8")
    return path
