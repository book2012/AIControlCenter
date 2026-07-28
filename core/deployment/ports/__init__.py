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

__all__ = (
    "CaddyDesiredStatePort",
    "ClockPort",
    "ColimaContractPort",
    "ComposeDesiredStatePort",
    "FileContentReadPort",
    "GitIdentityPort",
    "LaunchdObservationPort",
    "RuntimeMetadataPort",
)
