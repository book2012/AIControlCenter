"""Deterministic, stdlib-only wheels for our three pure-Python adapter packages.

No downloads, dynamic source execution, build hooks or automatic installation.
Format: https://packaging.python.org/en/latest/specifications/binary-distribution-format/
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {"shopping": "aicc_plugin_shopping", "creative-notes": "aicc_plugin_creative_notes",
            "personal-assistant": "aicc_plugin_personal_assistant"}

VERSIONS = {"shopping": "0.5.0", "creative-notes": "0.1.0", "personal-assistant": "0.2.0"}


def build_wheel(plugin_id, output, *, root=ROOT):
    package = PACKAGES[plugin_id]
    plugin = Path(root) / "plugins" / plugin_id
    config = json.loads((plugin / "distribution.json").read_text())
    expected = {"distribution": package.replace("_", "-"), "version": VERSIONS[plugin_id],
                "import_package": package, "requires": (["fastapi", "pydantic>=2,<3"] if plugin_id == "shopping" else ["fastapi"]), "platform_plugin_api": 1}
    if config != expected:
        raise ValueError("distribution must match the reviewed build allowlist")
    version = config["version"]
    members = {}
    source = plugin / "src" / package
    for path in sorted(source.rglob("*.py")):
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError("symlink source forbidden")
        if "__pycache__" in path.parts:
            continue
        members[package + "/" + path.relative_to(source).as_posix()] = path.read_bytes()
    if package + "/__init__.py" not in members:
        raise ValueError("package source missing")
    members[package + "/plugin_manifest.json"] = (plugin / "manifest.json").read_bytes()
    info = package + "-" + version + ".dist-info"
    metadata = ("Metadata-Version: 2.1\nName: " + config["distribution"] +
                "\nVersion: " + version + "\nSummary: Optional AIControlCenter platform adapter\n" +
                "Requires-Python: >=3.11\n" + "".join("Requires-Dist: " + item + "\n" for item in config["requires"]) + "\n" +
                "Requires a compatible AIControlCenter host API v1; not a standalone server.\n")
    members[info + "/METADATA"] = metadata.encode()
    members[info + "/WHEEL"] = b"Wheel-Version: 1.0\nGenerator: aicc-stdlib-plugin-builder\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    record = io.StringIO(newline="")
    writer = csv.writer(record, lineterminator="\n")
    for name in sorted(members):
        data = members[name]
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow([name, "sha256=" + digest, str(len(data))])
    writer.writerow([info + "/RECORD", "", ""])
    members[info + "/RECORD"] = record.getvalue().encode()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    wheel = output / (package + "-" + version + "-py3-none-any.whl")
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(members):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, members[name])
    return {"plugin_id": plugin_id, "version": version, "wheel": str(wheel), "size_bytes": wheel.stat().st_size,
            "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist/plugins")
    args = parser.parse_args()
    print(json.dumps({"schema_version": 1, "wheels": [build_wheel(x, args.output) for x in PACKAGES]}, indent=2))


if __name__ == "__main__":
    main()
