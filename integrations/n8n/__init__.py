"""Read-only n8n capability adapter."""

from .adapter import N8nAdapter, N8nConfiguration
from .composition import build_n8n_status_service

__all__ = ("N8nAdapter", "N8nConfiguration", "build_n8n_status_service")
