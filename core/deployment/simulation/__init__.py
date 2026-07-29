"""Pure, fake, non-production DPL-03D simulation composition."""

from core.deployment.simulation.executor import FakeDeploymentExecutor
from core.deployment.simulation.ports import ReplayGuard, SimulationExecutor, SimulationIntent
from core.deployment.simulation.receipt import SimulationExecutionReceiptBuilder
from core.deployment.simulation.replay import InMemoryReplayGuard
from core.deployment.simulation.service import SimulationApplyService
from core.deployment.simulation.validation import SimulationValidationResult

__all__ = (
    "FakeDeploymentExecutor",
    "InMemoryReplayGuard",
    "ReplayGuard",
    "SimulationApplyService",
    "SimulationExecutionReceiptBuilder",
    "SimulationExecutor",
    "SimulationIntent",
    "SimulationValidationResult",
)
