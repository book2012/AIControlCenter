"""Deterministic fake executor; it cannot express or perform runtime commands."""

from __future__ import annotations

from core.deployment.contracts import sha256_digest

from .ports import SimulationIntent


class FakeDeploymentExecutor:
    executor_type = "fake"

    def execute(self, intents: tuple[SimulationIntent, ...]) -> tuple[dict, ...]:
        return tuple(
            {
                "action_id": intent.action_id,
                "action_type": intent.action_type,
                "target": intent.target,
                "dependency_ids": list(intent.dependency_ids),
                "status": "SIMULATED",
                "result_digest": sha256_digest(
                    {
                        "mode": "simulation",
                        "executor_type": self.executor_type,
                        "intent": {
                            "action_id": intent.action_id,
                            "action_type": intent.action_type,
                            "target": intent.target,
                            "dependency_ids": list(intent.dependency_ids),
                            "result_expectation": intent.result_expectation,
                        },
                    }
                ),
            }
            for intent in intents
        )


__all__ = ("FakeDeploymentExecutor",)
