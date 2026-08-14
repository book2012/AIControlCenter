"""Read-only OpenClaw capability adapter."""

from .adapter import OpenClawAdapter, OpenClawConfiguration
from .composition import build_openclaw_status_service

__all__ = ("OpenClawAdapter", "OpenClawConfiguration", "build_openclaw_status_service")
