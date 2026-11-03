"""Compatibility alias for the shopping plugin-owned domain implementation."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module("aicc_plugin_shopping.customer_auth")
