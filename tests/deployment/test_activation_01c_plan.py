from dataclasses import fields

import pytest

from core.deployment.production_runtime_activation.models import (
    ProductionRuntimeActivationError,
)
from core.deployment.production_runtime_activation.plan import (
    PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE,
    ProductionRuntimeActivationPlan,
    activation_plan_digest,
)

SOURCE_DIGEST = (
    "sha256:"
    "a2b40bf8efb889e2a1e4b0185b175859716809be9bcbe45d73b4bfb991fe0792"
)


def plan(**overrides):
    values = {
        "candidate_runtime_id": "28869898a28f",
        "candidate_source_commit":
            "28869898a28fbc0f0d0fd6c995104defa645ada3",
        "source_artifact_content_digest": SOURCE_DIGEST,
        "governance_commit": "a" * 40,
        "expected_current_runtime_id": "d8f9f550093d",
        "canonical_service_label": "com.aicontrolcenter.api",
        "canonical_runtime_target": "ops.macos.runtime.application:app",
        "primitive_identity": PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE,
    }
    values.update(overrides)
    return ProductionRuntimeActivationPlan(**values)


def test_plan_binds_exact_source_artifact_and_fixed_primitive():
    value = plan()
    assert value.source_artifact_content_digest == SOURCE_DIGEST
    assert value.primitive_identity == PRODUCTION_RUNTIME_ACTIVATION_PRIMITIVE
    assert activation_plan_digest(value).startswith("sha256:")


def test_plan_digest_is_deterministic():
    assert activation_plan_digest(plan()) == activation_plan_digest(plan())


def test_plan_rejects_invalid_source_artifact_digest():
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="SOURCE_ARTIFACT_CONTENT_DIGEST_INVALID",
    ):
        plan(source_artifact_content_digest="sha256:not-a-valid-digest")


def test_plan_rejects_arbitrary_primitive_identity():
    with pytest.raises(
        ProductionRuntimeActivationError,
        match="ACTIVATION_PRIMITIVE_IDENTITY_INVALID",
    ):
        plan(primitive_identity="/bin/sh arbitrary-command")


def test_plan_exposes_no_raw_execution_surface():
    names = {item.name for item in fields(ProductionRuntimeActivationPlan)}
    assert names.isdisjoint({"shell", "argv", "environment", "command"})
