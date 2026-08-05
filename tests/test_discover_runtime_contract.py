from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PATH = ROOT / "ops/macos/runtime/discover-runtime-contract.py"
SPEC = importlib.util.spec_from_file_location(
    "discover_runtime_contract", DISCOVERY_PATH
)
assert SPEC is not None and SPEC.loader is not None
DISCOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISCOVERY)


def write_launchers(root: Path, *sources: str) -> None:
    for relative, source in zip(
        DISCOVERY.CANONICAL_RUNTIME_LAUNCHERS, sources, strict=True
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")


def test_canonical_launchers_agree_on_shadow_target() -> None:
    contract = DISCOVERY.discover_launcher_contract(ROOT)

    assert contract["agreed"] is True
    assert contract["selected_runtime_target"] == "core.api.shadow:app"
    assert contract["targets"] == ["core.api.shadow:app"]


def test_fastapi_application_objects_are_diagnostic_only(tmp_path: Path) -> None:
    app = tmp_path / "core/api/app.py"
    app.parent.mkdir(parents=True)
    app.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
    contract = DISCOVERY.discover_python_contract(tmp_path, [app])

    assert contract["inferred_runtime_targets"] == ["core.api.app:app"]
    assert "runtime_targets" not in contract


def test_launcher_disagreement_fails_closed(tmp_path: Path) -> None:
    write_launchers(
        tmp_path,
        "python -m uvicorn core.api.shadow:app\n",
        "python -m uvicorn core.api.other:app\n",
    )

    contract = DISCOVERY.discover_launcher_contract(tmp_path)
    assert contract["agreed"] is False
    assert contract["selected_runtime_target"] is None


def test_missing_launcher_target_fails_closed(tmp_path: Path) -> None:
    write_launchers(
        tmp_path,
        "echo no-target\n",
        "python -m uvicorn core.api.shadow:app\n",
    )

    contract = DISCOVERY.discover_launcher_contract(tmp_path)
    assert contract["selected_runtime_target"] is None
    assert contract["canonical_launchers"][0]["error"] == "launcher_target_missing"


def test_multiple_targets_in_launcher_fail_closed(tmp_path: Path) -> None:
    write_launchers(
        tmp_path,
        "python -m uvicorn core.api.shadow:app\npython -m uvicorn core.api.other:app\n",
        "python -m uvicorn core.api.shadow:app\n",
    )

    contract = DISCOVERY.discover_launcher_contract(tmp_path)
    assert contract["selected_runtime_target"] is None
    assert contract["canonical_launchers"][0]["error"] == "launcher_target_multiple"


def test_malformed_and_abbreviated_targets_are_rejected(tmp_path: Path) -> None:
    write_launchers(
        tmp_path,
        "python -m uvicorn app\n",
        "python -m uvicorn core.api.shadow-app\n",
    )

    contract = DISCOVERY.discover_launcher_contract(tmp_path)
    assert contract["selected_runtime_target"] is None
    assert {
        item["error"] for item in contract["canonical_launchers"]
    } == {"launcher_target_malformed"}


def test_health_endpoints_are_paths_deduplicated_and_deterministic(
    tmp_path: Path,
) -> None:
    source = tmp_path / "core/api/routes.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            (
                '@app.get("status")',
                '@app.get("healthy")',
                '@app.get("approval_status")',
                '@app.get("KeepAlive")',
                '@app.get("http://localhost:8000/health")',
                '@app.get("")',
                '@app.get("//health")',
                '@app.get("/runtime/health")',
                '@app.get("/health")',
                '@app.get("/health")',
                "def endpoint(): pass",
            )
        ),
        encoding="utf-8",
    )

    first = DISCOVERY.discover_python_contract(tmp_path, [source])
    second = DISCOVERY.discover_python_contract(tmp_path, [source])
    expected = [
        {"file": "core/api/routes.py", "method": "GET", "path": "/health"},
        {
            "file": "core/api/routes.py",
            "method": "GET",
            "path": "/runtime/health",
        },
    ]
    assert first["health_endpoints"] == expected
    assert second["health_endpoints"] == expected
