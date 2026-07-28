from __future__ import annotations

import json
from pathlib import Path

from core.deployment.contracts import load_schema_registry, validate_contract_payload


def test_pure_validation_does_not_use_runtime_dependencies(monkeypatch) -> None:
    def prohibited(*args, **kwargs):
        raise AssertionError("runtime dependency used")

    monkeypatch.setattr("subprocess.run", prohibited)
    monkeypatch.setattr("socket.create_connection", prohibited)
    monkeypatch.setattr("pathlib.Path.is_symlink", prohibited)
    fixture = (
        Path(__file__).parents[1]
        / "fixtures"
        / "deployment"
        / "immutable-deployment-package.json"
    )
    payload = json.loads(fixture.read_text("utf-8"))
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name="ImmutableDeploymentPackage",
        payload=payload,
    )
