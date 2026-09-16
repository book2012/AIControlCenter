"""Deterministic, local-only SHOP_MEDIA_002 plan and isolated demo fixture data.

Does not generate images, contact a service, or modify the original 92-item
catalog. Re-running preserves completed generation records for identical plans.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "brands/orange-coco/assets/media"
SOURCE = ROOT / "brands/orange-coco/catalog"
DEST = SOURCE / "lookbook-preview"
CATEGORIES = ("top", "bottom", "outer", "dress", "bag", "acc")
PRESENTATION_TAGS = {
    "top": ["#상의", "#데일리", "#미니멀"], "bottom": ["#팬츠", "#클래식", "#심플"],
    "outer": ["#아우터", "#소프트", "#가을무드"], "dress": ["#원피스", "#페미닌", "#데일리룩"],
    "bag": ["#가방", "#미니멀", "#데일리백"], "acc": ["#액세서리", "#포인트", "#데일리"],
}
POSES = ("standing front", "three-quarter standing", "walking", "turning",
         "looking over shoulder", "sitting", "leaning", "hands in pockets",
         "adjusting sleeve", "browsing clothing rack", "holding outerwear",
         "natural candid", "window-side", "doorway", "full-body walking",
         "waist-up editorial", "standing front", "turning", "sitting", "walking")
HAIR = ("short copper pixie", "dark brown loose curls", "long black braids",
        "chin-length blonde bob", "auburn wavy shoulder-length hair", "black coily afro",
        "chestnut low bun", "silver straight bob", "dark brown shaved crop",
        "long honey-blonde waves", "black sleek ponytail", "red curly bob",
        "brown natural coils", "platinum short curls", "long dark straight hair",
        "salt-and-pepper cropped curls", "copper side braid", "dark curly updo",
        "blonde blunt fringe and ponytail", "chocolate-brown shag")
SKINS = ("fair freckled", "light olive", "deep brown", "medium golden brown",
         "warm beige", "dark ebony", "medium olive", "light peach")
BODIES = ("petite straight silhouette", "tall broad-shouldered athletic build",
          "plus-size curvy build", "average height soft rounded build", "tall slender build")
FACES = ("round face, broad nose, wide-set eyes", "angular jaw, high cheekbones, narrow nose",
         "oval face, full cheeks, arched eyebrows", "heart-shaped face, hooded eyes, soft jaw",
         "long face, prominent nose, straight eyebrows", "square face, almond eyes, full lips")
SETTINGS = ("ivory plaster boutique wall", "pale oak boutique doorway", "sunlit quiet stone lane",
            "cream linen studio backdrop", "apricot boutique courtyard", "pale oak bench beside a window",
            "warm cream exterior wall", "minimal boutique fitting area", "soft daylight window corner",
            "unbranded cream and apricot clothing rack")
COLORS = ("warm ivory", "pale apricot", "cocoa", "muted sage", "oatmeal", "dusty blue",
          "soft terracotta", "cream", "charcoal", "powder pink", "sand", "muted olive",
          "pale peach", "warm grey", "soft navy", "butter yellow", "mushroom", "natural ecru",
          "dusty rose", "chocolate brown")
GARMENTS = {
    "top": ["soft linen blouse", "natural cotton shirt", "classic collared blouse", "light fine knit pullover",
            "cream gathered top", "minimal oversized shirt", "soft round-neck knit cardigan worn closed",
            "natural sleeveless top", "wave-detail blouse", "daily cotton tee"] * 2,
    "bottom": ["natural wide-leg pants", "soft elastic-waist slacks", "cream flared skirt", "daily cotton pants",
               "minimal long skirt", "light linen pants", "classic straight-leg pants", "oatmeal relaxed pants",
               "wide-leg pants", "soft slacks", "cream flared skirt", "cotton pants", "long skirt", "linen pants",
               "straight-leg pants", "light blue straight denim jeans", "ecru denim jeans", "tailored knee-length shorts",
               "linen shorts", "cocoa pleated slacks"],
    "outer": ["soft knit cardigan", "light linen jacket", "natural daily zip jumper", "cream classic jacket",
              "minimal oversized jacket", "soft short cardigan", "light trench jacket", "natural knit outer cardigan",
              "soft knit cardigan", "linen jacket", "daily lightweight jumper", "cream classic jacket",
              "oversized jacket", "short cardigan", "trench jacket", "long wool coat", "soft short coat",
              "long trench coat", "light zip jumper", "fine-knit open cardigan"],
    "dress": ["natural linen daily dress", "soft flared dress", "cream shirt dress", "light midi dress",
              "oatmeal long dress", "minimal opaque slip dress", "daily cotton mini dress", "natural strap maxi dress",
              "soft gathered dress", "classic collared shirt dress"] * 2,
    "bag": ["minimal shoulder bag", "natural daily tote", "soft mini crossbody bag", "classic square bag",
            "light canvas tote", "cream mini handbag"] * 2 + ["apricot bucket bag", "cocoa bucket bag",
            "woven daily tote", "soft crescent shoulder bag", "compact crossbody bag", "pale mini top-handle bag",
            "cream canvas tote", "drawstring bucket bag"],
    "acc": ["minimal fine-line necklace", "soft silk scarf", "natural hoop earrings", "classic chain bracelet",
            "daily pendant necklace"] * 2 + ["cream sun hat", "cocoa leather belt", "warm tortoiseshell sunglasses",
            "minimal unbranded wristwatch", "apricot hair barrette", "ivory hair ribbon", "soft cotton bucket hat",
            "slender woven belt", "small pearl hair clip", "round warm-frame sunglasses"],
}
ADDITIONS = {
    "bottom": ["라이트 스트레이트 데님", "내추럴 에크루 데님", "클래식 버뮤다 쇼츠", "소프트 린넨 쇼츠", "코코아 플리츠 슬랙스"],
    "outer": ["내추럴 롱 코트", "소프트 숏 코트", "클래식 롱 트렌치", "라이트 집업 점퍼", "데일리 오픈 가디건"],
    "bag": ["애프리콧 버킷백", "코코아 버킷백", "내추럴 우븐 토트", "소프트 크레센트 숄더백", "데일리 크로스백", "라이트 미니 토트", "크림 캔버스 토트", "드로스트링 버킷백"],
    "acc": ["크림 선햇", "코코아 데일리 벨트", "웜 톤 선글라스", "미니멀 데일리 워치", "애프리콧 헤어 바레트", "아이보리 헤어 리본", "소프트 버킷햇", "내추럴 우븐 벨트", "미니 펄 헤어핀", "라운드 선글라스"],
}


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def prepare():
    bundles = {name: json.loads((SOURCE / (name + ".json")).read_text())
               for name in ("catalog", "pricing", "inventory", "collections", "homepage")}
    products = bundles["catalog"]["products"]
    for category, names in ADDITIONS.items():
        count = sum(p["category"] == category for p in products)
        for n, name in enumerate(names, count + 1):
            identifier = f"oc-demo-{category}-{n:04}"
            products.append({"id": identifier, "brand_id": "orange-coco", "is_demo": True,
                             "demo_batch_id": "orange-coco-v1", "name": name, "slug": identifier,
                             "category": category, "category_label": category.upper(),
                             "image_path": f"brands/orange-coco/assets/media/catalog/{category}/{identifier}.jpg",
                             "style_story": "오렌지 코코의 카테고리 룩북을 위한 데모 샘플입니다. 현재 구매는 지원하지 않습니다.",
                             "collections": [], "enabled": True})
            bundles["pricing"]["prices"][identifier] = {"currency": "KRW", "regular_price": 19000 + n * 1000,
                                                       "sale_price": None, "is_sale": False}
            bundles["inventory"]["inventory"][identifier] = {"track_inventory": False, "stock_quantity": 0,
                                                             "in_stock": True, "status": "in_stock"}
    bundles["catalog"]["product_count"] = len(products)
    bundles["catalog"]["preview_only"] = "SHOP_MEDIA_002; original 92 records preserved; 28 fictional demo additions"
    for name, payload in bundles.items():
        write(DEST / (name + ".json"), payload)
    previous_path = MEDIA / "SHOP_MEDIA_002.json"
    previous = {a["id"]: a for a in json.loads(previous_path.read_text())["assets"]} if previous_path.exists() else {}
    assets = []
    for c, category in enumerate(CATEGORIES):
        selected = sorted((p for p in products if p["category"] == category), key=lambda p: p["id"])
        assert len(selected) == 20
        for i, product in enumerate(selected):
            product_only = (category == "bag" and i % 2 == 1) or (category == "acc" and i not in (1, 4, 10, 12, 14))
            profile = None if product_only else {
                "identity": f"fictional-adult-{category}-{i + 1:02}", "age": 25 + (i * 3 + c * 7) % 29,
                "gender": "woman", "face": FACES[(i + c) % len(FACES)],
                "skin_tone": SKINS[(i + c * 3) % len(SKINS)], "body_shape": BODIES[(i + c * 2) % len(BODIES)],
                "hairstyle_and_color": HAIR[(i + c * 7) % len(HAIR)],
                "expression": ("quiet smile", "thoughtful relaxed gaze", "natural candid laugh", "calm direct gaze")[(i + c) % 4],
            }
            pose = ("product flat lay", "product upright three-quarter", "product detail close-up", "product side profile")[i % 4] if product_only else POSES[(i + c * 3) % 20]
            if category == "dress" and not product_only:
                pose = ("full-body walking", "turning", "three-quarter standing", "doorway", "looking over shoulder")[i % 5]
            if category == "bag" and not product_only:
                pose = ("walking with bag worn", "sitting with bag held", "standing with bag on shoulder", "turning with crossbody bag", "leaning holding bag")[(i // 2) % 5]
            if category == "acc" and not product_only:
                pose = "natural model-worn accessory detail"
            crop = ("overhead detail, entire object visible" if i % 2 else "three-quarter product close-up, entire object visible") if product_only else (
                "full body head to shoes, lower garment unobstructed" if category == "bottom" else
                "full body head to shoes, dress hem visible" if category == "dress" else
                "close detail of accessory on adult model" if category == "acc" else
                "full body with bag prominent" if category == "bag" else
                "waist-up editorial with complete top visible" if i % 3 == 0 else "full body head to shoes")
            setting = SETTINGS[(i + c * 2) % len(SETTINGS)]
            if product_only:
                setting = ("ivory linen on pale oak", "warm cream plaster pedestal", "matte apricot paper on oak", "cream stone tabletop")[i % 4]
            color = COLORS[(i + c * 3) % 20]
            garment = GARMENTS[category][i]
            if "cream" in garment:
                color = "warm cream"
            elif "oatmeal" in garment:
                color = "oatmeal"
            subject = "No people; a single unbranded " + garment if product_only else (
                "One entirely original fictional adult woman, age {age}, {face}, {skin_tone} skin, {body_shape}, "
                "{hairstyle_and_color}, {expression}.".format(**profile) + " Featured item: " + garment)
            prompt = (f"Use case: {'product-mockup' if product_only else 'photorealistic-natural'}. "
                      f"Create one portrait 2:3 fashion ecommerce photograph for a warm Korean boutique category lookbook. "
                      f"Subject: {subject}. Item color: {color}. Pose: {pose}. Camera/crop: {crop}. "
                      f"Scene: {setting}. Soft natural daylight, warm ivory, cream, cocoa and restrained apricot palette; "
                      "believable fabric texture, editorial feminine modern approachable styling, realistic anatomy. "
                      "One image, no collage. Keep the featured category item clearly visible and in focus. "
                      "Supporting clothes are simple unbranded neutrals. "
                      "Western fashion editorial appearance with a fictional individual face; do not imply real ancestry. "
                      "No celebrity likeness, no real-person reference, no logos, no watermarks, no writing, no advertising campaign imitation. "
                      "Natural skin texture, varied individual face, no plastic skin, no oversaturation, tasteful adult everyday fashion.")
            identifier = product["id"]
            asset = {"id": identifier, "product_id": identifier, "category": category.upper(), "title": product["name"],
                     "model_profile": profile, "pose": pose, "camera_crop": crop, "setting": setting,
                     "garment": garment, "garment_color": color, "shot_type": "product-only" if product_only else "model-worn",
                     "presentation_tags": PRESENTATION_TAGS[category],
                     "generation_prompt": prompt, "generation_tool": "image_gen.imagegen", "status": "PLANNED",
                     "source": None,
                     "preferred_sources": ["ai_generated", "pexels_stock"],
                     "target_path": f"brands/orange-coco/assets/media/catalog/{category}/{identifier}.jpg",
                     "photo_route": f"/homepage/assets/storefront/catalog/{category}/{identifier}.jpg",
                     "sha256": None, "homepage_representative": i in (0, 5, 10, 15)}
            old = previous.get(identifier)
            if old and (old["generation_prompt"] == prompt or old["status"] == "GENERATED"):
                if old["status"] == "GENERATED":
                    prompt = old["generation_prompt"]
                    asset["generation_prompt"] = prompt
                asset.update({k: old[k] for k in ("status", "sha256", "generation_artifact", "generation_date", "visual_review") if k in old})
                if asset["status"] == "GENERATED":
                    asset["source"] = {"type": "ai_generated", "provider": "OpenAI built-in image generator",
                                        "source_url": None, "photographer": None, "source_photo_id": asset.get("generation_artifact", {}).get("filename"),
                                        "retrieval_date": asset.get("generation_date"), "local_target_path": asset["target_path"]}
            elif old and old["status"] != "PLANNED":
                raise ValueError("Refusing to silently replace a completed generation plan")
            asset["visual_policy_audit"] = "KEEP" if category == "top" and asset["status"] == "GENERATED" else None
            assets.append(asset)
    completed = [a for a in assets if a["status"] in {"GENERATED", "STOCK_IMPORTED"}]
    counts = {"target_count": len(assets), "completed_count": len(completed),
              "planned_count": sum(a["status"] == "PLANNED" for a in assets)}
    source_distribution = {"ai_generated": sum(a.get("source", {}).get("type") == "ai_generated" for a in completed if a.get("source")),
                           "stock": sum(a.get("source", {}).get("type") == "stock" for a in completed if a.get("source"))}
    write(previous_path, {"schema_version": 1, "sprint": "SHOP_MEDIA_002_CATEGORY_LOOKBOOK", "brand_id": "orange-coco",
                          "plan_created": "2026-09-14", "generation_policy": "One original built-in generation per asset. Fictional adults only. No remote assets.",
                          "catalog_fixture": "brands/orange-coco/catalog/lookbook-preview", "target_per_category": 20,
                          "original_catalog_unchanged": True, "homepage_samples_per_category": 4,
                          "legacy_fallback_active": False,
                          "legacy_deletion_inventory": "docs/architecture/SHOP-MEDIA-002R1-LEGACY-DELETION-CANDIDATES.json",
                          "visual_policy": {"top_keep": 20, "top_replace_for_new_art_direction": 0},
                          **counts, "source_distribution": {**source_distribution, "unverified_planned": counts["planned_count"]}, "assets": assets})
    print("Prepared 120 planned assets and 120 dev-only canonical demo records (92 preserved, 28 added).")


if __name__ == "__main__":
    prepare()
