"""Compatibility catalog exports; other provider ports remain host-owned."""
from aicc_plugin_shopping.catalog_ports import (
    CatalogReadQueryError, CatalogReadUnavailable, CommerceCatalogPort,
    Product, HealthFailureCode, Protocol,
)
__all__ = ("CatalogReadQueryError", "CatalogReadUnavailable", "CommerceCatalogPort",
           "Product", "HealthFailureCode", "Protocol")
