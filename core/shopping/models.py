from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    slug: str
    description: str
    price: Decimal
    currency: str
    category: str
    in_stock: bool
    source: str
    image_url: str | None = None
