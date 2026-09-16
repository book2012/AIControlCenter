"""Register an inspected built-in image output; encode with native sips.

This is an asset import, not an image-generation client. No network access.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "brands/orange-coco/assets/media/SHOP_MEDIA_002.json"


def record(identifier: str, source: Path, review: str):
    source = source.resolve(strict=True)
    if source.suffix != ".png" or "generated_images" not in source.parts:
        raise ValueError("Expected a local built-in generated PNG artifact")
    manifest = json.loads(MANIFEST.read_text())
    asset = next(a for a in manifest["assets"] if a["id"] == identifier)
    target = ROOT / asset["target_path"]
    if asset["status"] != "PLANNED" or target.exists():
        raise ValueError("Asset already exists; replacement requires explicit review")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if any(a.get("generation_artifact", {}).get("sha256") == source_hash for a in manifest["assets"]):
        raise ValueError("Duplicate generated artifact mapping")
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", str(source), "--out", str(target)],
                   check=True, capture_output=True)
    data = target.read_bytes()
    if not data.startswith(b"\xff\xd8\xff") or not data.endswith(b"\xff\xd9"):
        raise ValueError("Invalid JPEG encoding")
    asset.update(status="GENERATED", sha256=hashlib.sha256(data).hexdigest(),
                 generation_artifact={"filename": source.name, "sha256": source_hash},
                 generation_date=datetime.now(timezone.utc).date().isoformat(), visual_review=review)
    completed_items = [item for item in manifest["assets"] if item["status"] in {"GENERATED", "STOCK_IMPORTED"}]
    completed = len(completed_items)
    planned = sum(item["status"] == "PLANNED" for item in manifest["assets"])
    manifest.update(target_count=len(manifest["assets"]), completed_count=completed,
                    planned_count=planned,
                    source_distribution={"ai_generated": sum(item.get("source", {}).get("type") == "ai_generated" for item in completed_items if item.get("source")),
                                         "stock": sum(item.get("source", {}).get("type") == "stock" for item in completed_items if item.get("source")),
                                         "unverified_planned": planned})
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{identifier}: GENERATED, {len(data)} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifier")
    parser.add_argument("source", type=Path)
    parser.add_argument("--review", required=True)
    args = parser.parse_args()
    record(args.identifier, args.source, args.review)
