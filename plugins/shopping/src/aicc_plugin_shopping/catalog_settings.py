"""Public configuration projection. No environment, provider URL or credential fields."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogSettings:
    enabled: bool = True
    environment: str = "isolated_preview"
    runtime: str = "virtual"
    deployment_target: str = "mac-mini-m4"
    write_mode: str = "read_only"
    approval_required: bool = True
    automation_enabled: bool = False
    ai_enabled: bool = False
    catalog_adapter: str = "mock"

    @property
    def write_mode_supported(self):
        return self.write_mode in {"read_only", "draft", "approval_required", "controlled_write", "automated"}

    @property
    def catalog_adapter_supported(self):
        return self.catalog_adapter in {"mock", "woocommerce"}
