from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from core.deployment.bootstrap_evidence_recovery import (
    BootstrapEvidenceRecoveryConfig, BootstrapEvidenceRecoveryValidator,
)
from tests.support.operational_snapshot_factory import (
    ENVIRONMENT_KEYS, OperationalSnapshotFactory,
)


def repository_state(root: Path):
    return tuple((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest())
                 for path in sorted(root.rglob("*.py")) if path.is_file())


def test_factory_private_tmp_executor_binding_validation_and_repository_immutability():
    repository = Path(__file__).parents[2]
    before = repository_state(repository)
    result = OperationalSnapshotFactory(repository).create({})
    owned = result.root
    try:
        assert str(result.root).startswith("/private/tmp/test-infra-02-")
        assert all(path.is_relative_to(result.root) for path in (
            result.operational_snapshot, result.evidence_snapshot, result.recovery_work))
        assert result.production_authorized is False
        recovery = result.root / "second-validation"
        recovery.mkdir(mode=0o700)
        report = BootstrapEvidenceRecoveryValidator(BootstrapEvidenceRecoveryConfig(
            result.operational_snapshot, result.evidence_snapshot, recovery,
            result.trusted_binding)).validate()
        assert report["evidence_chain_status"] == "VALID"
        assert report["ubuntu_participation"] is False
        assert report["production_authorization"] is False
        assert before == repository_state(repository)
    finally:
        result.cleanup()
    assert not owned.exists()


def test_explicit_environment_precedence_and_owned_root_only_cleanup():
    factory = OperationalSnapshotFactory(Path(__file__).parents[2])
    generated = factory.create({})
    try:
        explicit = factory.create(generated.environment)
        assert dict(explicit.environment) == dict(generated.environment)
        assert explicit.root == generated.recovery_work.parent
        explicit.cleanup()
        assert generated.root.exists()
    finally:
        generated.cleanup()


def test_partial_explicit_environment_fails_closed():
    with pytest.raises(ValueError, match="SNAPSHOT_ENVIRONMENT_INCOMPLETE"):
        OperationalSnapshotFactory(Path(__file__).parents[2]).create(
            {ENVIRONMENT_KEYS[0]: "/private/tmp/only-one"})
