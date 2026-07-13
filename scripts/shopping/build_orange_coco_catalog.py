#!/usr/bin/env python3

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(
    "deploy/shopping/wordpress/plugins/"
    "ai-shopping-storefront/assets/demo/"
    "orange-coco-v1/asset-manifest.json"
)

OUTPUT_DIR = Path("brands/orange-coco/catalog")

CATEGORY_LABELS = {
    "top": "TOP",
    "dress": "DRESS",
    "bottom": "BOTTOM",
    "outer": "OUTER",
    "bag": "BAG",
    "acc": "ACC",
}

PRODUCT_NAMES = {
    "top": [
        "소프트 린넨 블라우스",
        "내추럴 코튼 셔츠",
        "클래식 카라 블라우스",
        "라이트 데일리 니트",
        "크림 셔링 탑",
        "미니멀 오버핏 셔츠",
        "소프트 라운드 니트",
        "내추럴 슬리브리스",
        "웨이브 블라우스",
        "데일리 코튼 티",
    ],
    "dress": [
        "내추럴 린넨 원피스",
        "소프트 플레어 드레스",
        "크림 셔츠 원피스",
        "라이트 미디 드레스",
        "오트밀 롱 원피스",
        "미니멀 슬립 드레스",
        "데일리 코튼 원피스",
        "내추럴 스트랩 드레스",
        "소프트 셔링 원피스",
        "클래식 카라 드레스",
    ],
    "bottom": [
        "내추럴 와이드 팬츠",
        "소프트 밴딩 슬랙스",
        "크림 플레어 스커트",
        "데일리 코튼 팬츠",
        "미니멀 롱 스커트",
        "라이트 린넨 팬츠",
        "클래식 스트레이트 팬츠",
        "오트밀 밴딩 팬츠",
    ],
    "outer": [
        "소프트 니트 가디건",
        "라이트 린넨 재킷",
        "내추럴 데일리 아우터",
        "크림 클래식 재킷",
        "미니멀 오버핏 재킷",
        "소프트 숏 가디건",
        "라이트 트렌치 재킷",
        "내추럴 니트 아우터",
    ],
    "bag": [
        "미니멀 숄더백",
        "내추럴 데일리 토트백",
        "소프트 미니 크로스백",
        "클래식 스퀘어 백",
        "라이트 캔버스백",
        "크림 미니백",
    ],
    "acc": [
        "미니멀 라인 네크리스",
        "소프트 실크 스카프",
        "내추럴 링 이어링",
        "클래식 체인 브레이슬릿",
        "데일리 포인트 네크리스",
    ],
}

STYLE_STORIES = [
    "부드러운 색감과 자연스러운 실루엣이 일상에 편안하게 어울리는 아이템입니다.",
    "과하지 않은 디테일과 차분한 분위기로 오래 즐기기 좋은 데일리 셀렉션입니다.",
    "가볍고 자연스러운 무드로 단독 또는 레이어드 스타일에 활용하기 좋습니다.",
    "따뜻한 뉴트럴 컬러와 편안한 핏으로 매일 부담 없이 입기 좋습니다.",
]

STYLE_TIPS = [
    "아이보리와 베이지 계열을 함께 매치해 자연스러운 톤온톤 룩을 완성해보세요.",
    "심플한 가방과 낮은 굽 슈즈를 더하면 차분한 데일리 스타일이 완성됩니다.",
    "가벼운 액세서리 하나만 더해 미니멀한 포인트를 연출해보세요.",
    "비슷한 명도의 뉴트럴 컬러와 함께 코디하면 더욱 부드러운 인상을 줍니다.",
]

CATEGORY_PRICES = {
    "top": [29000, 32000, 35000, 39000, 42000, 45000],
    "dress": [49000, 52000, 59000, 65000, 69000, 79000],
    "bottom": [39000, 42000, 45000, 49000, 52000],
    "outer": [59000, 65000, 69000, 79000, 89000],
    "bag": [39000, 45000, 49000, 59000, 65000],
    "acc": [19000, 22000, 25000, 29000, 32000],
}

COLORS = {
    "top": ["IVORY", "BEIGE", "BLACK"],
    "dress": ["CREAM", "BEIGE", "BLACK"],
    "bottom": ["BEIGE", "BROWN", "BLACK"],
    "outer": ["IVORY", "CAMEL", "BLACK"],
    "bag": ["CREAM", "BROWN", "BLACK"],
    "acc": ["GOLD", "SILVER", "CREAM"],
}

SIZES = {
    "top": ["S", "M", "L"],
    "dress": ["S", "M", "L"],
    "bottom": ["S", "M", "L"],
    "outer": ["FREE"],
    "bag": ["FREE"],
    "acc": ["FREE"],
}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def sale_price(regular_price: int) -> int:
    return int((regular_price * 0.78) // 1000 * 1000)


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit(
            f"Manifest not found: {MANIFEST_PATH}"
        )

    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assets = manifest.get("assets", [])

    if len(assets) != 92:
        raise SystemExit(
            f"Expected 92 assets, found {len(assets)}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rng = random.Random(20260713)

    products: list[dict[str, Any]] = []
    pricing: dict[str, dict[str, Any]] = {}
    inventory: dict[str, dict[str, Any]] = {}

    category_indexes: dict[str, int] = defaultdict(int)

    for global_index, asset in enumerate(assets, start=1):
        product_id = asset["id"]
        category = asset["category"]
        category_index = category_indexes[category]
        category_indexes[category] += 1

        names = PRODUCT_NAMES[category]
        product_name = names[
            category_index % len(names)
        ]

        if category_index >= len(names):
            product_name += f" {category_index + 1}"

        prices = CATEGORY_PRICES[category]
        regular_price = prices[
            category_index % len(prices)
        ]

        is_new = global_index <= 24
        is_best = global_index % 4 == 0
        is_sale = global_index % 5 == 0

        collections = []

        if is_new:
            collections.append("new")

        if is_best:
            collections.append("best")

        if is_sale:
            collections.append("sale")

        collections.extend([
            "minimal",
            "natural",
        ])

        if category in {"top", "dress", "bottom"}:
            collections.append("weekend")

        if category in {"top", "bottom", "outer"}:
            collections.append("office")

        relative_asset_path = (
            "wp-content/plugins/"
            "ai-shopping-storefront/assets/demo/"
            "orange-coco-v1/"
            f"{asset['local_path']}"
        )

        products.append(
            {
                "id": product_id,
                "brand_id": "orange-coco",
                "is_demo": True,
                "demo_batch_id": "orange-coco-v1",
                "name": product_name,
                "slug": product_id,
                "category": category,
                "category_label": CATEGORY_LABELS[
                    category
                ],
                "image_path": relative_asset_path,
                "gallery": [
                    relative_asset_path
                ],
                "style_story": STYLE_STORIES[
                    (global_index - 1)
                    % len(STYLE_STORIES)
                ],
                "style_tip": STYLE_TIPS[
                    (global_index - 1)
                    % len(STYLE_TIPS)
                ],
                "colors": COLORS[category],
                "sizes": SIZES[category],
                "collections": collections,
                "enabled": True,
                "source_asset_id": asset["id"],
            }
        )

        pricing[product_id] = {
            "currency": "KRW",
            "regular_price": regular_price,
            "sale_price": (
                sale_price(regular_price)
                if is_sale
                else None
            ),
            "is_sale": is_sale,
        }

        quantity = rng.randint(2, 24)

        if global_index in {17, 58}:
            quantity = 0

        inventory[product_id] = {
            "track_inventory": True,
            "stock_quantity": quantity,
            "in_stock": quantity > 0,
            "status": (
                "in_stock"
                if quantity > 0
                else "out_of_stock"
            ),
        }

    new_ids = [
        product["id"]
        for product in products
        if "new" in product["collections"]
    ]

    best_ids = [
        product["id"]
        for product in products
        if "best" in product["collections"]
    ]

    sale_ids = [
        product["id"]
        for product in products
        if "sale" in product["collections"]
    ]

    collections_payload = {
        "schema_version": 1,
        "brand_id": "orange-coco",
        "demo_batch_id": "orange-coco-v1",
        "collections": {
            "new": {
                "label": "NEW",
                "product_ids": new_ids,
            },
            "best": {
                "label": "BEST",
                "product_ids": best_ids,
            },
            "sale": {
                "label": "SALE",
                "product_ids": sale_ids,
            },
            "minimal": {
                "label": "MINIMAL",
                "product_ids": [
                    product["id"]
                    for product in products
                    if "minimal"
                    in product["collections"]
                ],
            },
            "weekend": {
                "label": "WEEKEND",
                "product_ids": [
                    product["id"]
                    for product in products
                    if "weekend"
                    in product["collections"]
                ],
            },
            "office": {
                "label": "OFFICE",
                "product_ids": [
                    product["id"]
                    for product in products
                    if "office"
                    in product["collections"]
                ],
            },
        },
    }

    homepage_sections = [
        {
            "id": "new",
            "type": "collection",
            "title": "New Arrivals",
            "limit": 8,
        },
        {
            "id": "best",
            "type": "collection",
            "title": "Best Sellers",
            "limit": 8,
        },
        {
            "id": "lookbook",
            "type": "lookbook",
            "enabled": False,
        },
        {
            "id": "top",
            "type": "category",
            "title": "Top",
            "limit": 8,
        },
        {
            "id": "dress",
            "type": "category",
            "title": "Dress",
            "limit": 8,
        },
        {
            "id": "sale",
            "type": "collection",
            "title": "Sale",
            "limit": 8,
        },
        {
            "id": "outer",
            "type": "category",
            "title": "Outer",
            "limit": 8,
        },
        {
            "id": "bag",
            "type": "category",
            "title": "Bag",
            "limit": 8,
        },
    ]

    write_json(
        OUTPUT_DIR / "catalog.json",
        {
            "schema_version": 1,
            "brand_id": "orange-coco",
            "is_demo_catalog": True,
            "demo_batch_id": "orange-coco-v1",
            "product_count": len(products),
            "products": products,
        },
    )

    write_json(
        OUTPUT_DIR / "pricing.json",
        {
            "schema_version": 1,
            "brand_id": "orange-coco",
            "prices": pricing,
        },
    )

    write_json(
        OUTPUT_DIR / "inventory.json",
        {
            "schema_version": 1,
            "brand_id": "orange-coco",
            "inventory": inventory,
        },
    )

    write_json(
        OUTPUT_DIR / "collections.json",
        collections_payload,
    )

    write_json(
        OUTPUT_DIR / "homepage.json",
        {
            "schema_version": 1,
            "brand_id": "orange-coco",
            "hero": {
                "title": (
                    "Dress beautifully. "
                    "Live beautifully."
                ),
                "cta_label": "Explore Collection",
                "cta_target": "#orange-coco-products",
            },
            "editorial": {
                "enabled": False,
            },
            "sections": homepage_sections,
        },
    )

    print({
        "products": len(products),
        "new": len(new_ids),
        "best": len(best_ids),
        "sale": len(sale_ids),
        "out_of_stock": sum(
            1
            for item in inventory.values()
            if not item["in_stock"]
        ),
        "output_directory": str(OUTPUT_DIR),
    })


if __name__ == "__main__":
    main()
