"""Typed read-only ports for DPL composition."""

from .audit import AuditEvidenceSinkPort

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
    "AuditEvidenceSinkPort",
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
