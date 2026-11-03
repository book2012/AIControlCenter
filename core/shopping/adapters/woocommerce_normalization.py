"""Host schema/policy composition for plugin-owned canonical normalization."""
from pathlib import Path
from aicc_plugin_shopping.adapters import woocommerce_normalization as _implementation
from core.shopping.adapters.woocommerce_commerce_read import WooCommerceCommerceReadAdapter, WooCommerceCommerceReadError
from core.shopping.contracts.schema_validation import load_canonical_schema_catalog, validate_instance

WooCommerceRawReadPort = _implementation.WooCommerceRawReadPort
_RawCatalogFacade = _implementation._RawCatalogFacade
_RawOrderFacade = _implementation._RawOrderFacade


class WooCommerceCanonicalNormalizer(_implementation.WooCommerceCanonicalNormalizer):
    def __init__(self, *, currency_code, currency_minor_unit, schema_root=None):
        # Preserve configuration rejection before any schema filesystem lookup.
        super().__init__(currency_code=currency_code, currency_minor_unit=currency_minor_unit,
                         validate=lambda schema_id, value: False)
        catalog = load_canonical_schema_catalog(schema_root=schema_root)
        self._catalog = catalog
        self._validate_callback = lambda schema_id, value: validate_instance(catalog=catalog, schema_id=schema_id, instance=value).accepted


def build_woocommerce_commerce_read_adapter(
    *,
    vendor: WooCommerceRawReadPort,
    currency_code: str,
    currency_minor_unit: int,
    schema_root: Path | None = None,
) -> WooCommerceCommerceReadAdapter:
    normalizer = WooCommerceCanonicalNormalizer(
        currency_code=currency_code,
        currency_minor_unit=currency_minor_unit,
        schema_root=schema_root,
    )
    return WooCommerceCommerceReadAdapter(
        catalog=_RawCatalogFacade(vendor),
        order_reader=_RawOrderFacade(vendor),
        cursor_page_decoder=normalizer.decode_cursor,
        product_normalizer=normalizer.normalize_product,
        product_page_normalizer=normalizer.normalize_page,
        order_summary_normalizer=normalizer.normalize_order,
    )



def __getattr__(name):
    return getattr(_implementation, name)

__all__ = tuple(name for name in vars(_implementation) if not name.startswith("_"))
