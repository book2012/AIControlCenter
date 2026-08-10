from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from core.governance.control_plane.contracts import CONTRACT_NAMES, load_contract_registry
from core.governance.control_plane.domain import (
    GovernanceAuthorizationConsumptionReceipt, GovernanceAuthorizationDecision,
    GovernanceAuthorizationReceipt, GovernanceAuthorizationRequest,
    GovernanceAuthorizationStateRecord, GovernanceEvidenceBundle,
    GovernanceEvidenceManifest, GovernanceExecutionReceipt, GovernanceExecutionRequest,
    GovernanceFailureEvidence, GovernanceMutationBudget, GovernancePostconditionReport,
    GovernancePreconditionSnapshot,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "contracts" / "v1"
MODEL_TYPES = {
    cls.__name__: cls for cls in (
        GovernanceAuthorizationRequest, GovernancePreconditionSnapshot,
        GovernanceAuthorizationDecision, GovernanceAuthorizationReceipt,
        GovernanceAuthorizationStateRecord, GovernanceMutationBudget,
        GovernanceAuthorizationConsumptionReceipt, GovernanceExecutionRequest,
        GovernanceExecutionReceipt, GovernancePostconditionReport,
        GovernanceFailureEvidence, GovernanceEvidenceManifest, GovernanceEvidenceBundle,
    )
}


def _fixtures(kind: str) -> dict[str, Path]:
    suffix = f".{kind}.json"
    return {path.name.removesuffix(suffix): path for path in sorted((FIXTURE_ROOT / kind).glob(f"*{suffix}"))}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    json.dumps(value, allow_nan=False, sort_keys=True)
    return value


def test_fixture_names_map_exactly_to_registry_contracts() -> None:
    assert set(_fixtures("valid")) == set(CONTRACT_NAMES)
    assert set(_fixtures("invalid")) == set(CONTRACT_NAMES)
    assert len(_fixtures("valid")) == len(_fixtures("invalid")) == 16


@pytest.mark.parametrize("contract_name", CONTRACT_NAMES)
def test_valid_fixture_passes(contract_name: str) -> None:
    validator = Draft202012Validator(load_contract_registry().contract_schema(contract_name))
    assert not tuple(validator.iter_errors(_load(_fixtures("valid")[contract_name])))


@pytest.mark.parametrize("contract_name", CONTRACT_NAMES)
def test_invalid_fixture_fails(contract_name: str) -> None:
    validator = Draft202012Validator(load_contract_registry().contract_schema(contract_name))
    assert tuple(validator.iter_errors(_load(_fixtures("invalid")[contract_name])))


@pytest.mark.parametrize("contract_name,model_type", MODEL_TYPES.items())
def test_model_backed_fixture_uses_current_projection_shape(contract_name: str, model_type: type) -> None:
    fixture_keys = set(_load(_fixtures("valid")[contract_name]))
    model_keys = {field.name for field in fields(model_type)}
    if contract_name == "GovernanceMutationBudget":
        model_keys.add("remaining_count")
    assert fixture_keys == model_keys
