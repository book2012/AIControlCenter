from __future__ import annotations

import dataclasses
import json
import stat
from pathlib import Path

import pytest

from core.deployment.bootstrap_evidence_recovery import (
    BootstrapEvidenceRecoveryConfig, BootstrapEvidenceRecoveryError,
    BootstrapEvidenceRecoveryValidator, ControlledBootstrapEvidenceGenerator,
    ControlledEvidenceInput,
)
from core.deployment.bootstrap_evidence_recovery.generator import ControlledBootstrapEvidenceGenerator as Generator
from core.deployment.contracts import canonical_json_bytes
from tests.support.operational_snapshot_factory import OperationalSnapshotFactory


def specification(path: Path) -> ControlledEvidenceInput:
    return ControlledEvidenceInput(
        path, "synthetic-requester", "synthetic-operator",
        "synthetic-independent-approver", "focused-generator-seed")


def test_generator_exact_canonical_secret_free_artifact_set_and_modes():
    root = Path("/private/tmp/test-infra-02-generator-focused")
    if root.exists():
        pytest.fail("controlled test root unexpectedly exists")
    try:
        result = ControlledBootstrapEvidenceGenerator().generate(specification(root))
        assert {path.name for path in root.iterdir()} == set(Generator.ARTIFACTS)
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        for path in root.iterdir():
            raw = path.read_bytes()
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
            assert canonical_json_bytes(json.loads(raw)) == raw
            lowered = raw.lower()
            assert all(marker not in lowered for marker in (
                b"password", b"api_key", b"access_token", b"/users/", b"library/logs"))
        assert result.receipt["production_authorized"] is False
        assert result.trusted_binding.authorization_id not in specification(root).identity_seed
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.trusted_binding.permit_id = "changed"
    finally:
        if root.exists():
            import shutil
            shutil.rmtree(root)


def test_validator_rejects_missing_wrong_and_evidence_self_assertion():
    factory = OperationalSnapshotFactory(Path(__file__).parents[2])
    with factory.create({}) as snapshot:
        def config(binding):
            recovery = snapshot.root / ("validation-" + str(len(tuple(snapshot.root.iterdir()))))
            recovery.mkdir(mode=0o700)
            return BootstrapEvidenceRecoveryConfig(
                snapshot.operational_snapshot, snapshot.evidence_snapshot, recovery, binding)

        with pytest.raises(BootstrapEvidenceRecoveryError, match="TRUSTED_BINDING_REQUIRED"):
            BootstrapEvidenceRecoveryValidator(config(None)).validate()
        wrong = dataclasses.replace(snapshot.trusted_binding,
                                    permit_digest="sha256:" + "0" * 64)
        with pytest.raises(BootstrapEvidenceRecoveryError, match="PERMIT_DIGEST_INVALID"):
            BootstrapEvidenceRecoveryValidator(config(wrong)).validate()
        asserted = json.loads((snapshot.evidence_snapshot / "operational-permit.json").read_bytes())
        assert asserted["permit_digest"] == snapshot.trusted_binding.permit_digest
        with pytest.raises(BootstrapEvidenceRecoveryError, match="TRUSTED_BINDING_REQUIRED"):
            BootstrapEvidenceRecoveryValidator(config(None)).validate()


@pytest.mark.parametrize(("environment", "authorized"), [
    ("production", False), ("CONTROLLED_NON_PRODUCTION", True)])
def test_generator_rejects_production_environment_and_authorization(environment, authorized):
    with pytest.raises(BootstrapEvidenceRecoveryError, match="CONTROLLED_EVIDENCE_INPUT_REJECTED"):
        ControlledEvidenceInput(
            Path("/private/tmp/test-infra-02-rejected"), "requester", "operator",
            "approver", "seed", environment=environment,
            production_authorized=authorized)
