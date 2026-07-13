#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import requests


ROOT = Path(
    "deploy/shopping/wordpress/plugins/"
    "ai-shopping-storefront/assets/demo/orange-coco-v1"
)

CONFIG_PATH = Path(
    "scripts/shopping/orange_coco_demo_queries.json"
)

MANIFEST_PATH = ROOT / "asset-manifest.json"

PEXELS_API_URL = "https://api.pexels.com/v1/search"


def search_photos(
    api_key: str,
    query: str,
    page: int,
) -> list[dict]:
    response = requests.get(
        PEXELS_API_URL,
        headers={
            "Authorization": api_key,
            "User-Agent": "AIControlCenter-OrangeCoco/1.0",
        },
        params={
            "query": query,
            "orientation": "portrait",
            "size": "large",
            "page": page,
            "per_page": 40,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json().get("photos", [])


def download_image(
    image_url: str,
    destination: Path,
) -> str:
    response = requests.get(
        image_url,
        headers={
            "User-Agent": "AIControlCenter-OrangeCoco/1.0",
        },
        timeout=60,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    if not content_type.startswith("image/"):
        raise RuntimeError(
            f"Unexpected content type: {content_type}"
        )

    if len(response.content) < 20_000:
        raise RuntimeError(
            f"Image too small: {destination.name}"
        )

    temporary = destination.with_suffix(".jpg.part")
    temporary.write_bytes(response.content)
    temporary.replace(destination)

    return hashlib.sha256(
        response.content
    ).hexdigest()


def main() -> None:
    api_key = os.environ.get(
        "PEXELS_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise SystemExit(
            "PEXELS_API_KEY 환경변수가 설정되지 않았습니다."
        )

    config = json.loads(
        CONFIG_PATH.read_text(encoding="utf-8")
    )

    used_source_ids: set[int] = set()
    manifest_assets: list[dict] = []

    for category, settings in config.items():
        required_count = int(settings["count"])
        output_directory = ROOT / "products" / category

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for existing_file in output_directory.glob(
            "oc-demo-*.jpg"
        ):
            existing_file.unlink()

        selected: list[dict] = []

        for query in settings["queries"]:
            for page in range(1, 5):
                photos = search_photos(
                    api_key,
                    query,
                    page,
                )

                for photo in photos:
                    source_id = int(photo["id"])

                    if source_id in used_source_ids:
                        continue

                    width = int(photo.get("width", 0))
                    height = int(photo.get("height", 0))

                    if width <= 0 or height <= width:
                        continue

                    source = photo.get("src", {})

                    image_url = (
                        source.get("portrait")
                        or source.get("large2x")
                    )

                    if not image_url:
                        continue

                    used_source_ids.add(source_id)

                    selected.append(
                        {
                            "photo": photo,
                            "query": query,
                            "image_url": image_url,
                        }
                    )

                    if len(selected) >= required_count:
                        break

                if len(selected) >= required_count:
                    break

                time.sleep(0.2)

            if len(selected) >= required_count:
                break

        if len(selected) < required_count:
            raise RuntimeError(
                f"{category}: required={required_count}, "
                f"found={len(selected)}"
            )

        for index, selected_item in enumerate(
            selected,
            start=1,
        ):
            asset_id = (
                f"oc-demo-{category}-{index:04d}"
            )

            destination = (
                output_directory / f"{asset_id}.jpg"
            )

            checksum = download_image(
                selected_item["image_url"],
                destination,
            )

            photo = selected_item["photo"]

            manifest_assets.append(
                {
                    "id": asset_id,
                    "brand_id": "orange-coco",
                    "is_demo": True,
                    "demo_batch_id": "orange-coco-v1",
                    "category": category,
                    "local_path": str(
                        destination.relative_to(ROOT)
                    ),
                    "source": "pexels",
                    "source_photo_id": int(photo["id"]),
                    "source_page_url": photo.get("url"),
                    "photographer": photo.get(
                        "photographer"
                    ),
                    "photographer_url": photo.get(
                        "photographer_url"
                    ),
                    "search_query": selected_item["query"],
                    "alt": photo.get("alt", ""),
                    "width": int(photo.get("width", 0)),
                    "height": int(photo.get("height", 0)),
                    "sha256": checksum,
                }
            )

            print(
                f"{category.upper():7s} "
                f"{index:02d}/{required_count:02d} "
                f"{destination.name}"
            )

    manifest = {
        "schema_version": 1,
        "brand_id": "orange-coco",
        "is_demo_catalog": True,
        "demo_batch_id": "orange-coco-v1",
        "asset_count": len(manifest_assets),
        "assets": manifest_assets,
    }

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        {
            "asset_count": len(manifest_assets),
            "manifest": str(MANIFEST_PATH),
        }
    )


if __name__ == "__main__":
    main()
