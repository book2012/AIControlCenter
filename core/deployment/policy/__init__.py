"""Pure dependency-boundary policy services for DPL."""

from .dependency_boundaries import (
    DependencyBoundaryPolicyError,
    validate_dependency_boundaries,
)

__all__ = ("DependencyBoundaryPolicyError", "validate_dependency_boundaries")
