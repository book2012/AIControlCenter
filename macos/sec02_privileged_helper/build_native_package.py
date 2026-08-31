#!/usr/bin/env python3
"""Build the exact unsigned SEC-02 native application package."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from macos.sec02_privileged_helper.validate_package import (
    APP_EXECUTABLE,
    EXPECTED,
    HELPER_EXECUTABLE,
    PackageContractError,
    load_contract,
    validate_templates,
)

ROOT = Path(__file__).resolve().parent
SOURCES = {
    APP_EXECUTABLE: (ROOT / "NativeFoundation.swift", ROOT / "AppMain.swift"),
    HELPER_EXECUTABLE: (
        ROOT / "NativeFoundation.swift",
        ROOT / "SEC02HelperService.swift",
        ROOT / "HelperMain.swift",
    ),
}
EXPECTED_FILES = frozenset({
    "Contents/Info.plist",
    f"Contents/MacOS/{APP_EXECUTABLE}",
    f"Contents/MacOS/{HELPER_EXECUTABLE}",
    f"Contents/Library/LaunchDaemons/{EXPECTED['launchdaemon_plist_name']}",
})
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",
    b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",
}
LC_SEGMENT = 0x1
LC_SEGMENT_64 = 0x19
LC_CODE_SIGNATURE = 0x1D
HELPER_INFO_PLIST = ROOT / "templates" / "Helper-Info.plist"


def _is_macho(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(4) in MACHO_MAGICS


def _inspect_thin_macho(path: Path) -> tuple[bytes | None, bool]:
    data = path.read_bytes()
    formats = {
        b"\xce\xfa\xed\xfe": ("<", False),
        b"\xfe\xed\xfa\xce": (">", False),
        b"\xcf\xfa\xed\xfe": ("<", True),
        b"\xfe\xed\xfa\xcf": (">", True),
    }
    try:
        endian, is_64 = formats[data[:4]]
    except KeyError as error:
        raise PackageContractError("native artifact is not a supported thin Mach-O") from error
    header_size = 32 if is_64 else 28
    if len(data) < header_size:
        raise PackageContractError("truncated Mach-O header")
    ncmds, sizeofcmds = struct.unpack_from(f"{endian}II", data, 16)
    commands_end = header_size + sizeofcmds
    if commands_end > len(data):
        raise PackageContractError("truncated Mach-O load commands")
    offset = header_size
    info_plist = None
    has_code_signature = False
    for _ in range(ncmds):
        if offset + 8 > commands_end:
            raise PackageContractError("invalid Mach-O load command")
        command, command_size = struct.unpack_from(f"{endian}II", data, offset)
        if command_size < 8 or offset + command_size > commands_end:
            raise PackageContractError("invalid Mach-O load command size")
        if command == LC_CODE_SIGNATURE:
            has_code_signature = True
        expected_command = LC_SEGMENT_64 if is_64 else LC_SEGMENT
        if command == expected_command:
            segment_header_size = 72 if is_64 else 56
            section_size = 80 if is_64 else 68
            if command_size < segment_header_size:
                raise PackageContractError("invalid Mach-O segment command")
            nsects_offset = offset + (64 if is_64 else 48)
            nsects = struct.unpack_from(f"{endian}I", data, nsects_offset)[0]
            if segment_header_size + nsects * section_size > command_size:
                raise PackageContractError("invalid Mach-O section table")
            for index in range(nsects):
                section = offset + segment_header_size + index * section_size
                section_name = data[section:section + 16].split(b"\0", 1)[0]
                segment_name = data[section + 16:section + 32].split(b"\0", 1)[0]
                if section_name == b"__info_plist" and segment_name == b"__TEXT":
                    if is_64:
                        size = struct.unpack_from(f"{endian}Q", data, section + 40)[0]
                        file_offset = struct.unpack_from(f"{endian}I", data, section + 48)[0]
                    else:
                        size, file_offset = struct.unpack_from(f"{endian}II", data, section + 36)
                    if file_offset + size > len(data):
                        raise PackageContractError("embedded helper Info.plist is truncated")
                    info_plist = data[file_offset:file_offset + size]
        offset += command_size
    if offset != commands_end:
        raise PackageContractError("Mach-O load command size mismatch")
    return info_plist, has_code_signature


def _validate_unsigned_macho(path: Path) -> None:
    _, has_code_signature = _inspect_thin_macho(path)
    if has_code_signature:
        raise PackageContractError(f"{path.name} unexpectedly contains LC_CODE_SIGNATURE")


def _validate_helper_metadata(path: Path) -> dict:
    raw_plist, _ = _inspect_thin_macho(path)
    if raw_plist is None:
        raise PackageContractError("helper executable has no embedded Info.plist")
    try:
        info = plistlib.loads(raw_plist)
    except Exception as error:
        raise PackageContractError("helper embedded Info.plist is invalid") from error
    expected = {
        "CFBundleExecutable": HELPER_EXECUTABLE,
        "CFBundleIdentifier": EXPECTED["helper_bundle_identifier"],
        "CFBundlePackageType": "BNDL",
    }
    if info != expected:
        raise PackageContractError("helper embedded Info.plist metadata mismatch")
    return info


def _validate_exact_layout(bundle: Path) -> None:
    actual = {
        str(path.relative_to(bundle))
        for path in bundle.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual != EXPECTED_FILES:
        raise PackageContractError("native bundle layout mismatch")
    for name in (APP_EXECUTABLE, HELPER_EXECUTABLE):
        executable = bundle / "Contents" / "MacOS" / name
        if executable.is_symlink() or executable.stat().st_size == 0 or not _is_macho(executable):
            raise PackageContractError(f"{name} is not a non-empty Mach-O executable")
        _validate_unsigned_macho(executable)
    _validate_helper_metadata(bundle / "Contents" / "MacOS" / HELPER_EXECUTABLE)


def build_native(destination: Path, *, swiftc: Path | None = None) -> dict:
    load_contract()
    validate_templates()
    if not destination.is_absolute() or destination.name != "AIControlCenter.app":
        raise PackageContractError("destination must be an absolute AIControlCenter.app path")
    if destination.exists():
        raise PackageContractError("destination already exists")
    compiler = swiftc or Path(subprocess.run(
        ["xcrun", "--find", "swiftc"], check=True, text=True,
        capture_output=True,
    ).stdout.strip())
    if not compiler.is_absolute() or not compiler.is_file():
        raise PackageContractError("selected Swift compiler is not an absolute file")
    sdk = Path(subprocess.run(
        ["xcrun", "--show-sdk-path"], check=True, text=True,
        capture_output=True,
    ).stdout.strip())
    if not sdk.is_absolute() or not sdk.is_dir():
        raise PackageContractError("selected macOS SDK is not an absolute directory")

    contents = destination / "Contents"
    executable_dir = contents / "MacOS"
    daemon_dir = contents / "Library" / "LaunchDaemons"
    try:
        executable_dir.mkdir(parents=True)
        daemon_dir.mkdir(parents=True)
        shutil.copyfile(ROOT / "templates" / "App-Info.plist", contents / "Info.plist")
        shutil.copyfile(
            ROOT / "templates" / "LaunchDaemon.plist",
            daemon_dir / EXPECTED["launchdaemon_plist_name"],
        )
        with tempfile.TemporaryDirectory(
            prefix="sec02-swift-cache-", dir="/private/tmp"
        ) as cache:
            compiler_environment = os.environ.copy()
            compiler_environment["CLANG_MODULE_CACHE_PATH"] = cache
            for name, sources in SOURCES.items():
                command = [
                    os.fspath(compiler),
                    "-sdk", os.fspath(sdk),
                    "-module-cache-path", cache,
                    "-Xlinker", "-no_adhoc_codesign",
                ]
                if name == HELPER_EXECUTABLE:
                    command.extend([
                        "-Xlinker", "-sectcreate",
                        "-Xlinker", "__TEXT",
                        "-Xlinker", "__info_plist",
                        "-Xlinker", os.fspath(HELPER_INFO_PLIST),
                    ])
                command.extend([
                    "-o", os.fspath(executable_dir / name),
                    *(os.fspath(source) for source in sources),
                ])
                subprocess.run(command, check=True, env=compiler_environment)
        _validate_exact_layout(destination)
        info = plistlib.loads((contents / "Info.plist").read_bytes())
        if info.get("CFBundleIdentifier") != EXPECTED["app_bundle_identifier"]:
            raise PackageContractError("native app bundle identifier mismatch")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise

    return {
        "app_executable": {"mach_o": True, "name": APP_EXECUTABLE, "non_empty": True},
        "bundle_layout_valid": True,
        "helper_executable": {"mach_o": True, "name": HELPER_EXECUTABLE, "non_empty": True},
        "native_executables_built": True,
        "production_mutation_performed": False,
        "registration_performed": False,
        "schema_version": 1,
        "signed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    evidence = build_native(args.destination)
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
