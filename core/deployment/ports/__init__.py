"""Typed read-only ports for DPL inventory collection."""

from .inventory import (
    CaddyDesiredStatePort,
    ClockPort,
    ColimaContractPort,
    ComposeDesiredStatePort,
    FileContentReadPort,
    GitIdentityPort,
    LaunchdObservationPort,
    RuntimeMetadataPort,
)
from .ingress import IngressContractPort, IngressEvidencePort

__all__ = (
    "CaddyDesiredStatePort",
    "ClockPort",
    "ColimaContractPort",
    "ComposeDesiredStatePort",
    "FileContentReadPort",
    "GitIdentityPort",
    "LaunchdObservationPort",
    "RuntimeMetadataPort",
    "IngressContractPort",
    "IngressEvidencePort",
)
