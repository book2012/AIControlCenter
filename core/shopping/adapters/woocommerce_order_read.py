"""Compatibility alias for plugin-owned provider/domain mapping."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module("aicc_plugin_shopping.adapters.woocommerce_order_read")
