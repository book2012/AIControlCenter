"""Review-gated Codex product intake and isolated DEV WooCommerce registration."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from io import BytesIO


JOB_ID = re.compile(r"^[a-f0-9]{8}$")
CATEGORIES = {"top", "bottom", "outer", "dress", "bag", "acc"}
MEDIA = {
    "hero": (".jpg", "image/jpeg", b"\xff\xd8\xff"),
    "original": (".jpg", "image/jpeg", b"\xff\xd8\xff"),
    "model-front": (".jpg", "image/jpeg", b"\xff\xd8\xff"),
    "garment-cutout": (".webp", "image/webp", b"RIFF"),
    "model-other": (".jpg", "image/jpeg", b"\xff\xd8\xff"),
}
MAX_MEDIA_BYTES = 8 * 1024 * 1024
CATEGORY_LABELS = {"top": "TOP", "bottom": "BOTTOM", "outer": "OUTER", "dress": "DRESS", "bag": "BAG", "acc": "ACC"}


class ProductIntakeError(ValueError):
    pass


class DevProductIntake:
    """Keep user uploads private and invoke the existing registrar only after review."""

    def __init__(self, *, root: Path, source: Path, revision: str, runner=None):
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ProductIntakeError("PINNED_DEV_REVISION_REQUIRED")
        self.root = Path(root)
        self.source = Path(source)
        self.revision = revision
        self.runner = runner or self._run
        self.lock = threading.RLock()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ProductIntakeError("PRIVATE_INTAKE_ROOT_INVALID")
        os.chmod(self.root, 0o700)

    @staticmethod
    def _run(argv, *, timeout=120, **kwargs):
        text_mode = kwargs.pop("text", True)
        try:
            return subprocess.run(argv, capture_output=True, text=text_mode, timeout=timeout, check=False, **kwargs)
        except (OSError, subprocess.TimeoutExpired):
            raise ProductIntakeError("DEV_PRODUCT_OPERATION_UNAVAILABLE") from None

    def _job_dir(self, job_id: str) -> Path:
        if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            raise ProductIntakeError("PRODUCT_JOB_ID_INVALID")
        path = self.root / job_id
        if path.is_symlink():
            raise ProductIntakeError("PRODUCT_JOB_PATH_INVALID")
        path.mkdir(mode=0o700, exist_ok=True)
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise ProductIntakeError("PRODUCT_JOB_PATH_INVALID")
        return path

    @staticmethod
    def _read_meta(path: Path) -> dict:
        target = path / "review.json"
        if target.is_symlink():
            raise ProductIntakeError("PRODUCT_REVIEW_INVALID")
        if not target.exists():
            return {"state": "COLLECTING", "media": {}}
        try:
            value = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ProductIntakeError("PRODUCT_REVIEW_INVALID") from None
        if not isinstance(value, dict) or not isinstance(value.get("media"), dict):
            raise ProductIntakeError("PRODUCT_REVIEW_INVALID")
        return value

    @staticmethod
    def _write_meta(path: Path, value: dict) -> None:
        target = path / "review.json"
        fd, temp_name = tempfile.mkstemp(prefix=".review-", dir=path)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def upload_media(self, job_id: str, role: str, body: bytes, *, content_type: str, filename: str, ai_generated: bool) -> dict:
        if role not in MEDIA or not isinstance(body, bytes) or not 1 <= len(body) <= MAX_MEDIA_BYTES:
            raise ProductIntakeError("PRODUCT_MEDIA_BOUNDS")
        extension, expected_type, signature = MEDIA[role]
        if content_type.split(";", 1)[0].strip().lower() != expected_type:
            raise ProductIntakeError("PRODUCT_MEDIA_TYPE_INVALID")
        if role == "garment-cutout":
            if body[:4] != signature or body[8:12] != b"WEBP":
                raise ProductIntakeError("PRODUCT_MEDIA_SIGNATURE_INVALID")
        elif not body.startswith(signature):
            raise ProductIntakeError("PRODUCT_MEDIA_SIGNATURE_INVALID")
        if type(ai_generated) is not bool or (role == "original" and ai_generated):
            raise ProductIntakeError("PRODUCT_MEDIA_PROVENANCE_INVALID")
        clean_name = Path(filename or "").name
        clean_name = re.sub(r"[^A-Za-z0-9._-]", "_", clean_name)[:120] or "upload" + extension
        with self.lock:
            directory = self._job_dir(job_id)
            meta = self._read_meta(directory)
            if meta.get("state") in {"APPLYING", "REGISTERED", "APPLY_OUTCOME_UNKNOWN"}:
                raise ProductIntakeError("PRODUCT_REVIEW_LOCKED")
            target = directory / ("media-" + role + extension)
            if target.is_symlink():
                raise ProductIntakeError("PRODUCT_MEDIA_PATH_INVALID")
            fd, temp_name = tempfile.mkstemp(prefix=".media-", dir=directory)
            try:
                os.fchmod(fd, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(body)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp_name, target)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
            item = {"filename": clean_name, "sha256": hashlib.sha256(body).hexdigest(),
                    "ai_generated": ai_generated, "bytes": len(body)}
            meta.setdefault("media", {})[role] = item
            meta["state"] = "COLLECTING"
            self._write_meta(directory, meta)
            return {"role": role, "filename": clean_name, "sha256": item["sha256"], "bytes": len(body)}

    def save_review(self, job_id: str, fields: dict) -> dict:
        required = {"name", "category", "description", "style_tip", "price", "sale_price", "price_basis",
                    "tags", "option_type", "color_options", "size_options", "inventory", "inventory_pending"}
        if not isinstance(fields, dict) or set(fields) != required:
            raise ProductIntakeError("PRODUCT_REVIEW_FIELDS_INVALID")
        name, category, description, style_tip = (fields.get(k) for k in ("name", "category", "description", "style_tip"))
        if type(name) is not str or not name.strip() or len(name) > 200:
            raise ProductIntakeError("PRODUCT_NAME_INVALID")
        if category not in CATEGORIES:
            raise ProductIntakeError("PRODUCT_CATEGORY_INVALID")
        if type(description) is not str or not description.strip() or len(description) > 20000:
            raise ProductIntakeError("PRODUCT_DESCRIPTION_INVALID")
        if type(style_tip) is not str or len(style_tip) > 1000:
            raise ProductIntakeError("PRODUCT_STYLE_TIP_INVALID")
        price = fields.get("price")
        sale = fields.get("sale_price")
        if type(price) is not int or not 1 <= price <= 10_000_000:
            raise ProductIntakeError("PRODUCT_PRICE_INVALID")
        if sale is not None and (type(sale) is not int or not 1 <= sale < price):
            raise ProductIntakeError("PRODUCT_SALE_PRICE_INVALID")
        if fields.get("price_basis") not in {"user_set", "user_authorized", "user_authorized_temporary"}:
            raise ProductIntakeError("PRODUCT_PRICE_BASIS_INVALID")
        tags = fields.get("tags")
        if not isinstance(tags, list) or len(tags) > 40 or any(type(v) is not str or not v.strip() or len(v) > 80 for v in tags) or len(tags) != len(set(tags)):
            raise ProductIntakeError("PRODUCT_TAGS_INVALID")
        pending = fields.get("inventory_pending")
        if type(pending) is not bool:
            raise ProductIntakeError("PRODUCT_INVENTORY_STATE_INVALID")
        option_type = fields.get("option_type")
        colors, sizes, inventory = fields.get("color_options"), fields.get("size_options"), fields.get("inventory")
        if option_type not in {"color", "size", "color_size"} or not isinstance(colors, list) or not isinstance(sizes, list) or not isinstance(inventory, dict):
            raise ProductIntakeError("PRODUCT_OPTIONS_INVALID")
        try:
            from core.shopping.product_registration import _option_rows
            _option_rows(fields)
        except (ImportError, ValueError, TypeError):
            raise ProductIntakeError("PRODUCT_OPTIONS_INVALID") from None
        normalized = dict(fields)
        normalized["name"] = name.strip()
        with self.lock:
            directory = self._job_dir(job_id)
            meta = self._read_meta(directory)
            if meta.get("state") in {"APPLYING", "REGISTERED", "APPLY_OUTCOME_UNKNOWN"}:
                raise ProductIntakeError("PRODUCT_REVIEW_LOCKED")
            if meta.get("catalog_id") and isinstance(meta.get("fields"), dict) and meta["fields"].get("category") != normalized["category"]:
                raise ProductIntakeError("PRODUCT_CATEGORY_LOCKED_AFTER_PREFLIGHT")
            meta.update({"fields": normalized, "state": "REVIEW_SAVED", "updated_at": time.time()})
            self._write_meta(directory, meta)
            return self.status(job_id)

    def status(self, job_id: str) -> dict:
        directory = self._job_dir(job_id)
        meta = self._read_meta(directory)
        return {"job_id": job_id, "state": meta.get("state", "COLLECTING"),
                "fields": meta.get("fields"), "media": meta.get("media", {}),
                "catalog_id": meta.get("catalog_id"), "preflight": meta.get("preflight"), "receipt": meta.get("receipt")}

    def _reserve_catalog_id(self, job_id: str, category: str) -> str:
        if category not in CATEGORIES or not self.source.is_dir() or self.source.is_symlink():
            raise ProductIntakeError("DEV_PRODUCT_SOURCE_INVALID")
        catalog_path = "brands/agachichi/catalog/dev-upload-products.json"
        raw = self._run(["git", "-C", str(self.source), "show", f"{self.revision}:{catalog_path}"], timeout=30)
        if raw.returncode:
            raise ProductIntakeError("DEV_CATALOG_INVALID")
        try:
            catalog = json.loads(raw.stdout)
            rows = catalog.get("products")
        except (json.JSONDecodeError, AttributeError):
            raise ProductIntakeError("DEV_CATALOG_INVALID") from None
        if catalog.get("environment") != "DEV" or catalog.get("schema_version") != 1 or not isinstance(rows, list):
            raise ProductIntakeError("DEV_CATALOG_INVALID")
        pattern = re.compile(r"^ag-upload-" + re.escape(category) + r"-([0-9]{4})$")
        existing = [int(match.group(1)) for row in rows if isinstance(row, dict)
                    and isinstance(row.get("id"), str) and (match := pattern.fullmatch(row["id"]))]
        db_path = self.root / "catalog-id-reservations.sqlite3"
        if db_path.is_symlink():
            raise ProductIntakeError("PRODUCT_ID_RESERVATION_INVALID")
        try:
            with sqlite3.connect(db_path, timeout=10) as db:
                db.execute("CREATE TABLE IF NOT EXISTS reservations(job_id TEXT PRIMARY KEY, category TEXT NOT NULL, catalog_id TEXT NOT NULL UNIQUE)")
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT category,catalog_id FROM reservations WHERE job_id=?", (job_id,)).fetchone()
                if row:
                    if row[0] != category:
                        raise ProductIntakeError("PRODUCT_ID_BINDING_CHANGED")
                    return row[1]
                reserved = db.execute("SELECT catalog_id FROM reservations WHERE category=?", (category,)).fetchall()
                reserved_numbers = [int(match.group(1)) for (value,) in reserved
                                    if (match := pattern.fullmatch(value))]
                number = max(existing + reserved_numbers, default=0) + 1
                if number > 9999:
                    raise ProductIntakeError("PRODUCT_ID_EXHAUSTED")
                catalog_id = f"ag-upload-{category}-{number:04d}"
                db.execute("INSERT INTO reservations VALUES(?,?,?)", (job_id, category, catalog_id))
            os.chmod(db_path, 0o600)
            return catalog_id
        except sqlite3.Error:
            raise ProductIntakeError("PRODUCT_ID_RESERVATION_FAILED") from None

    def _workspace(self, job_id: str, meta: dict, workspace: Path) -> str:
        if not self.source.is_dir() or self.source.is_symlink():
            raise ProductIntakeError("DEV_PRODUCT_SOURCE_INVALID")
        check = self.runner(["git", "-C", str(self.source), "cat-file", "-e", self.revision + "^{commit}"], timeout=20)
        if check.returncode:
            raise ProductIntakeError("DEV_PRODUCT_REVISION_UNAVAILABLE")
        archive = self.runner(["git", "-C", str(self.source), "archive", "--format=tar", self.revision], timeout=60, text=False)
        if archive.returncode:
            raise ProductIntakeError("DEV_PRODUCT_ARCHIVE_FAILED")
        try:
            with tarfile.open(fileobj=BytesIO(archive.stdout), mode="r:") as bundle:
                bundle.extractall(workspace, filter="data")
        except (tarfile.TarError, OSError, ValueError):
            raise ProductIntakeError("DEV_PRODUCT_ARCHIVE_INVALID") from None
        fields = meta.get("fields")
        if not isinstance(fields, dict):
            raise ProductIntakeError("PRODUCT_REVIEW_REQUIRED")
        media = meta.get("media", {})
        if set(media) != set(MEDIA):
            raise ProductIntakeError("PRODUCT_MEDIA_INCOMPLETE")
        catalog_path = workspace / "brands/agachichi/catalog/dev-upload-products.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        rows = catalog.get("products")
        if catalog.get("environment") != "DEV" or catalog.get("schema_version") != 1 or not isinstance(rows, list):
            raise ProductIntakeError("DEV_CATALOG_INVALID")
        category = fields["category"]
        catalog_id = meta.get("catalog_id") or self._reserve_catalog_id(job_id, category)
        if not isinstance(catalog_id, str) or not re.fullmatch(r"ag-upload-" + re.escape(category) + r"-[0-9]{4}", catalog_id):
            raise ProductIntakeError("PRODUCT_ID_BINDING_CHANGED")
        if any(isinstance(row, dict) and row.get("id") == catalog_id for row in rows):
            raise ProductIntakeError("PRODUCT_ID_CONFLICT")
        option_type = fields["option_type"]
        if option_type not in {"color", "size", "color_size"}:
            raise ProductIntakeError("PRODUCT_OPTION_TYPE_INVALID")
        inventory = fields["inventory"]
        if not isinstance(inventory, dict) or not inventory or len(inventory) > 100:
            raise ProductIntakeError("PRODUCT_INVENTORY_INVALID")
        expected_keys = None
        colors = fields["color_options"]
        sizes = fields["size_options"]
        if not isinstance(colors, list) or not isinstance(sizes, list):
            raise ProductIntakeError("PRODUCT_OPTIONS_INVALID")
        if option_type == "color":
            expected_keys = {v.get("id") for v in colors if isinstance(v, dict)}
        elif option_type == "size":
            expected_keys = {v.lower() for v in sizes if isinstance(v, str)}
        else:
            expected_keys = {f"{v.get('id')}--{s.lower()}" for v in colors if isinstance(v, dict) for s in sizes if isinstance(s, str)}
        if not expected_keys or set(inventory) != expected_keys:
            raise ProductIntakeError("PRODUCT_INVENTORY_OPTION_MISMATCH")
        if any(type(v) is not int or not 0 <= v <= 9999 for v in inventory.values()):
            raise ProductIntakeError("PRODUCT_INVENTORY_INVALID")
        if fields["inventory_pending"] and any(inventory.values()):
            raise ProductIntakeError("PENDING_INVENTORY_MUST_BE_ZERO")
        spec = {
            "id": catalog_id, "source": "user_upload", "name": fields["name"], "slug": catalog_id,
            "category": category, "category_label": CATEGORY_LABELS[category],
            "description": fields["description"], "style_tip": fields["style_tip"], "tags": fields["tags"],
            "collections": ["new"], "image_id": catalog_id, "price_status": "READY", "price": fields["price"],
            "sale_price": fields["sale_price"], "price_basis": fields["price_basis"], "currency": "KRW",
            "option_type": option_type, "color_options": colors, "size_options": sizes,
            "inventory": inventory, "inventory_pending": fields["inventory_pending"], "enabled": True,
            "registered_at": time.strftime("%Y-%m-%d"), "source_files": [media[role]["filename"] for role in MEDIA],
            "registration_method": "codex_reviewed_intake",
        }
        rows.append(spec)
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        upload_root = workspace / "brands/agachichi/assets/media/uploads"
        gallery_root = upload_root / "gallery"
        gallery_root.mkdir(parents=True, exist_ok=True)
        manifest_path = upload_root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("environment") != "DEV" or not isinstance(manifest.get("assets"), list):
            raise ProductIntakeError("DEV_MEDIA_MANIFEST_INVALID")
        asset_rows = manifest["assets"]
        hero_item = media["hero"]
        hero_rel = f"brands/agachichi/assets/media/uploads/{catalog_id}.jpg"
        hero_target = workspace / hero_rel
        shutil.copyfile(self._media_path(job_id, "hero"), hero_target)
        asset_rows.append({"id": catalog_id, "product_id": catalog_id, "category": CATEGORY_LABELS[category],
            "status": "READY", "target_path": hero_rel,
            "photo_route": f"/homepage/assets/storefront/catalog/{category}/{catalog_id}.jpg",
            "sha256": hero_item["sha256"],
            "source": {"type": "user_upload", "original_file_names": [hero_item["filename"]], "ai_generated": hero_item["ai_generated"], "processing": "User-reviewed upload; AI-generated status is recorded separately."}})
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        gallery_path = upload_root / "gallery.json"
        gallery_doc = json.loads(gallery_path.read_text(encoding="utf-8"))
        if gallery_doc.get("environment") != "DEV" or gallery_doc.get("schema_version") != 1 or not isinstance(gallery_doc.get("assets"), list):
            raise ProductIntakeError("DEV_GALLERY_MANIFEST_INVALID")
        kinds = ("original", "model-front", "garment-cutout", "model-other")
        for role in kinds:
            ext, _, _ = MEDIA[role]
            rel = f"brands/agachichi/assets/media/uploads/gallery/{catalog_id}-{role}{ext}"
            target = workspace / rel
            shutil.copyfile(self._media_path(job_id, role), target)
            gallery_doc["assets"].append({"product_id": catalog_id, "kind": role, "color_id": None,
                "path": rel, "sha256": media[role]["sha256"], "ai_generated": media[role]["ai_generated"]})
        gallery_path.write_text(json.dumps(gallery_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return catalog_id

    def _media_path(self, job_id: str, role: str) -> Path:
        ext = MEDIA[role][0]
        path = self._job_dir(job_id) / ("media-" + role + ext)
        if path.is_symlink() or not path.is_file():
            raise ProductIntakeError("PRODUCT_MEDIA_INCOMPLETE")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        meta = self._read_meta(path.parent)
        if meta.get("media", {}).get(role, {}).get("sha256") != digest:
            raise ProductIntakeError("PRODUCT_MEDIA_HASH_MISMATCH")
        return path

    def _run_registrar(self, job_id: str, meta: dict, *, apply: bool) -> dict:
        with tempfile.TemporaryDirectory(prefix="aicc-product-intake-") as temp:
            workspace = Path(temp)
            catalog_id = self._workspace(job_id, meta, workspace)
            argv = [sys.executable, str(workspace / "ops/macos/shopping/dev_upload_product_register.py"),
                    "--catalog-id", catalog_id]
            if apply:
                argv.append("--apply-dev")
            try:
                result = self.runner(argv, timeout=240, cwd=workspace)
            except Exception:
                raise ProductIntakeError("APPLY_OUTCOME_UNKNOWN" if apply else "DEV_PRODUCT_PREFLIGHT_FAILED") from None
            if result.returncode:
                raise ProductIntakeError("APPLY_OUTCOME_UNKNOWN" if apply else "DEV_PRODUCT_PREFLIGHT_FAILED")
            try:
                receipt = json.loads(result.stdout.strip().splitlines()[-1])
            except (json.JSONDecodeError, IndexError):
                raise ProductIntakeError("APPLY_OUTCOME_UNKNOWN" if apply else "DEV_PRODUCT_PREFLIGHT_RECEIPT_INVALID") from None
            if not isinstance(receipt, dict) or receipt.get("environment") != "DEV":
                raise ProductIntakeError("APPLY_OUTCOME_UNKNOWN" if apply else "DEV_PRODUCT_REGISTRATION_ENVIRONMENT_INVALID")
            expected = "REGISTERED" if apply else None
            if apply and (receipt.get("state") != expected or receipt.get("prod_mutation") is not False or receipt.get("activation") is not False):
                raise ProductIntakeError("APPLY_OUTCOME_UNKNOWN")
            if not apply and (receipt.get("mutation") is not False or receipt.get("activation") is not False or receipt.get("sku_state") != "SKU_AVAILABLE"):
                raise ProductIntakeError("DEV_PRODUCT_PREFLIGHT_RECEIPT_INVALID")
            return {"catalog_id": catalog_id, "receipt": receipt}

    def preflight(self, job_id: str) -> dict:
        with self.lock:
            directory = self._job_dir(job_id)
            meta = self._read_meta(directory)
            if meta.get("state") == "REGISTERED":
                return self.status(job_id)
            if not isinstance(meta.get("fields"), dict):
                raise ProductIntakeError("PRODUCT_REVIEW_REQUIRED")
            if set(meta.get("media", {})) != set(MEDIA):
                raise ProductIntakeError("PRODUCT_MEDIA_INCOMPLETE")
            reserved_id = self._reserve_catalog_id(job_id, meta["fields"]["category"])
            if meta.get("catalog_id") not in (None, reserved_id):
                raise ProductIntakeError("PRODUCT_ID_BINDING_CHANGED")
            meta["catalog_id"] = reserved_id
            self._write_meta(directory, meta)
            result = self._run_registrar(job_id, meta, apply=False)
            meta.update({"state": "READY_TO_REGISTER", "catalog_id": result["catalog_id"],
                         "preflight": result["receipt"], "updated_at": time.time()})
            self._write_meta(directory, meta)
            return self.status(job_id)

    def register(self, job_id: str, confirmation: str) -> dict:
        with self.lock:
            directory = self._job_dir(job_id)
            meta = self._read_meta(directory)
            if meta.get("state") == "REGISTERED":
                return self.status(job_id)
            if meta.get("state") == "APPLYING" or meta.get("state") == "APPLY_OUTCOME_UNKNOWN":
                raise ProductIntakeError("APPLY_OUTCOME_UNKNOWN")
            if meta.get("state") != "READY_TO_REGISTER" or not isinstance(meta.get("fields"), dict):
                raise ProductIntakeError("PRODUCT_PREFLIGHT_REQUIRED")
            name = meta["fields"]["name"]
            if type(confirmation) is not str or confirmation != name:
                raise ProductIntakeError("PRODUCT_CONFIRMATION_MISMATCH")
            meta.update({"state": "APPLYING", "apply_started_at": time.time()})
            self._write_meta(directory, meta)
            try:
                result = self._run_registrar(job_id, meta, apply=True)
            except ProductIntakeError as exc:
                meta["state"] = "APPLY_OUTCOME_UNKNOWN" if str(exc) == "APPLY_OUTCOME_UNKNOWN" else "APPLY_FAILED"
                self._write_meta(directory, meta)
                raise
            meta.update({"state": "REGISTERED", "receipt": result["receipt"], "updated_at": time.time()})
            self._write_meta(directory, meta)
            return self.status(job_id)
