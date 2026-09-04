from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

from core.shopping.observability.storage_continuity import (
    ContinuityCompleteness,
    ContinuityReason,
    StorageContinuityObservation,
    VolumeContinuitySnapshot,
)
from core.shopping.runtime_cutover_secret_source import (
    RuntimeCutoverSourceObservation,
    SourceReason,
)
from ops.macos.shopping import shop_service_start_01b_preflight as preflight
from ops.macos.shopping.shop_service_start_01b_preflight import collect_preflight


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "ops/macos/shopping/shop_service_start_01b_preflight.py"


def _runtime() -> dict[str, object]:
    return {"schema_version": "1.0", "inspection": "read-only", "ready": True}


def _storage() -> StorageContinuityObservation:
    return StorageContinuityObservation((VolumeContinuitySnapshot(
        "ai-shopping-database", True, "local", "local", "fixed-time", True,
        "/var/lib/mysql", "/var/lib/mysql", "volume", "database", "shopping-db",
        ContinuityCompleteness.COMPLETE, ContinuityReason.NONE,
    ),))


def _source() -> RuntimeCutoverSourceObservation:
    return RuntimeCutoverSourceObservation(
        "1.0", "fixed-authority", "runtime_cutover_variable_source", "fixed-path-role",
        True, ("SHOPPING_DB_PASSWORD",), (), (), (), True, SourceReason.READY,
        wordpress_port_value_valid=True,
    )


def test_collects_required_metadata_and_existing_observer_projections() -> None:
    payload = collect_preflight(
        runtime_observer=_runtime, storage_observer=_storage, source_observer=_source,
    )
    assert payload == {
        "schema_version": "1.0",
        "authoritative_work_item": "SHOP-SERVICE-START-01B",
        "inspection": "read-only",
        "mutation_performed": False,
        "authorization_created": False,
        "authorization_consumed": False,
        "production_authority": False,
        "ubuntu_authority": False,
        "runtime": _runtime(),
        "storage_continuity": _storage().to_json_safe(),
        "runtime_cutover_source": _source().projection(),
    }
    storage = payload["storage_continuity"]
    assert storage["evidence_kind"] == "volume_identity_observation"
    assert storage["volumes"][0]["expected_attachment"] is True
    assert storage["volumes"][0]["observed_destination"] == "/var/lib/mysql"


def test_source_projection_and_failures_are_value_free() -> None:
    secret = "never-emit-this-secret"

    def fail():
        raise RuntimeError(secret)

    payload = collect_preflight(
        runtime_observer=fail, storage_observer=fail, source_observer=fail,
    )
    encoded = json.dumps(payload, sort_keys=True)
    assert secret not in encoded
    assert payload["runtime_cutover_source"]["values_exposed"] is False
    assert all(payload[name]["error_type"] == "ObserverFailure" for name in (
        "runtime", "storage_continuity", "runtime_cutover_source",
    ))


def test_no_mutation_authorization_or_authority_surface() -> None:
    tree = ast.parse(ENTRYPOINT.read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    forbidden = {
        "Popen", "run", "system", "execute", "bootstrap", "remediate", "authorize",
        "create", "start", "stop", "restart", "up", "down",
    }
    assert not (names | attributes) & forbidden
    payload = collect_preflight(
        runtime_observer=_runtime, storage_observer=_storage, source_observer=_source,
    )
    assert payload["mutation_performed"] is False
    assert payload["authorization_created"] is False
    assert payload["authorization_consumed"] is False
    assert payload["production_authority"] is False
    assert payload["ubuntu_authority"] is False


def test_cli_is_directly_runnable_and_has_no_override_options() -> None:
    script = ENTRYPOINT.read_text(encoding="utf-8")
    assert "source-path" not in script and "trusted-home" not in script
    result = subprocess.run(
        ["python3", str(ENTRYPOINT), "--help"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0
    assert "never-emit" not in result.stdout + result.stderr


def test_main_emits_one_deterministic_json_object(monkeypatch, capsys) -> None:
    expected = collect_preflight(
        runtime_observer=_runtime, storage_observer=_storage, source_observer=_source,
    )
    monkeypatch.setattr(preflight, "collect_preflight", lambda: expected)
    assert preflight.main([]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == expected
    assert set(("runtime", "storage_continuity", "runtime_cutover_source")) <= set(payload)
