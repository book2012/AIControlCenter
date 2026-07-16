import json
from pathlib import Path

from core.runtime.metadata_generator import RuntimeMetadataGenerator

def test_runtime_metadata_generator_writes_metadata(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    generator = RuntimeMetadataGenerator(
        runtime_dir=runtime_dir,
        commit="67e617ebc469e36daa82e060c547bed78aec441c",
        short_commit="67e617ebc469",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    metadata_path = generator.write()
    data = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert metadata_path == runtime_dir / "metadata.json"
    assert data["schema_version"] == 1
    assert data["commit"] == "67e617ebc469e36daa82e060c547bed78aec441c"
    assert data["short_commit"] == "67e617ebc469"
    assert data["runtime_mode"] == "shadow"
    assert data["created_at"] == "2026-07-16T13:18:00Z"

def test_runtime_metadata_generator_creates_runtime_directory(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "missing" / "runtime"
    generator = RuntimeMetadataGenerator(
        runtime_dir=runtime_dir,
        commit="67e617ebc469e36daa82e060c547bed78aec441c",
        short_commit="67e617ebc469",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    metadata_path = generator.write()

    assert runtime_dir.is_dir()
    assert metadata_path.is_file()

def test_runtime_metadata_generator_writes_atomically(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    metadata_path = runtime_dir / "metadata.json"
    metadata_path.write_text("old", encoding="utf-8")

    generator = RuntimeMetadataGenerator(
        runtime_dir=runtime_dir,
        commit="67e617ebc469e36daa82e060c547bed78aec441c",
        short_commit="67e617ebc469",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    generator.write()

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert data["short_commit"] == "67e617ebc469"
    assert not (runtime_dir / ".metadata.json.tmp").exists()

def test_runtime_metadata_generator_rejects_invalid_commit(
    tmp_path: Path,
) -> None:
    generator = RuntimeMetadataGenerator(
        runtime_dir=tmp_path,
        commit="invalid",
        short_commit="invalid",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    try:
        generator.write()
    except ValueError as exc:
        assert "commit" in str(exc)
    else:
        raise AssertionError("ValueError was not raised")

def test_runtime_metadata_generator_rejects_short_commit_mismatch(
    tmp_path: Path,
) -> None:
    generator = RuntimeMetadataGenerator(
        runtime_dir=tmp_path,
        commit="67e617ebc469e36daa82e060c547bed78aec441c",
        short_commit="000000000000",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    try:
        generator.write()
    except ValueError as exc:
        assert "short_commit" in str(exc)
    else:
        raise AssertionError("ValueError was not raised")
