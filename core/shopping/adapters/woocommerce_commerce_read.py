"""Legacy constructor bridge: platform policy remains authoritative."""
from aicc_plugin_shopping.adapters import woocommerce_commerce_read as _implementation
from core.shopping.governance.external_read_policy import evaluate_external_read

WooCommerceCommerceReadError = _implementation.WooCommerceCommerceReadError


class WooCommerceCommerceReadAdapter(_implementation.WooCommerceCommerceReadAdapter):
    def __init__(self, *, catalog, order_reader, cursor_page_decoder, product_normalizer,
                 product_page_normalizer, order_summary_normalizer):
        super().__init__(catalog=catalog, order_reader=order_reader, cursor_page_decoder=cursor_page_decoder,
            product_normalizer=product_normalizer, product_page_normalizer=product_page_normalizer,
            order_summary_normalizer=order_summary_normalizer,
            authorize=lambda *, path, query: evaluate_external_read(provider="woocommerce", method="GET", path=path, query=query).allowed)


def __getattr__(name):
    return getattr(_implementation, name)

__all__ = tuple(name for name in vars(_implementation) if not name.startswith("_"))
