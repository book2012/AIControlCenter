import pytest

from core.deployment.production_runtime_activation.claim import (
    ProductionRuntimeActivationExecutionLaneRegistry,
)
from core.deployment.production_runtime_activation.models import (
    ProductionRuntimeActivationError,
)


def test_production_runtime_pointer_activation_is_serialized(tmp_path):
    root = tmp_path / "activation-lane"
    root.mkdir(mode=0o700)

    registry = ProductionRuntimeActivationExecutionLaneRegistry(root)

    with registry.acquire():
        with pytest.raises(
            ProductionRuntimeActivationError,
            match="ACTIVATION_EXECUTION_LANE_BUSY",
        ):
            with registry.acquire():
                pass
