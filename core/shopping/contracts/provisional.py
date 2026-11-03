"""Compatibility module alias preserving existing symbol and patch identity."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module("aicc_plugin_shopping.contracts.provisional")
