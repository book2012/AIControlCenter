import json
import os
from pathlib import Path

import pytest

from core.runtime.metadata_generator import RuntimeMetadataGenerator


COMMIT = "67e617ebc469e36daa82e060c547bed78aec441c"


def test_runtime_metadata_generator_writes_metadata(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    generator = RuntimeMetadataGenerator(
        runtime_dir=runtime_dir,
        commit=COMMIT,
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
    marker_path = runtime_dir / ".aicontrolcenter-source-commit"
    assert marker_path.is_file()
    assert marker_path.read_bytes() == (COMMIT + "\n").encode()
    assert sorted(path.name for path in runtime_dir.iterdir()) == [
        ".aicontrolcenter-source-commit",
        "metadata.json",
    ]


def test_runtime_metadata_generator_creates_runtime_directory(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "missing" / "runtime"
    generator = RuntimeMetadataGenerator(
        runtime_dir=runtime_dir,
        commit=COMMIT,
        short_commit="67e617ebc469",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    metadata_path = generator.write()

    assert runtime_dir.is_dir()
    assert metadata_path.is_file()


def test_runtime_metadata_generator_writes_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    metadata_path = runtime_dir / "metadata.json"
    real_replace = os.replace
    replacements: list[tuple[Path, Path]] = []

    def record_replace(source: Path, destination: Path) -> None:
        replacements.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", record_replace)

    generator = RuntimeMetadataGenerator(
        runtime_dir=runtime_dir,
        commit=COMMIT,
        short_commit="67e617ebc469",
        runtime_mode="shadow",
        created_at="2026-07-16T13:18:00Z",
    )

    generator.write()

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert data["short_commit"] == "67e617ebc469"
    assert [destination.name for _, destination in replacements] == [
        ".aicontrolcenter-source-commit",
        "metadata.json",
    ]
    assert not any(path.name.endswith(".tmp") for path in runtime_dir.iterdir())


def test_runtime_metadata_generator_does_not_repair_existing_release(
    tmp_path: Path,
) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text("existing", encoding="utf-8")
    generator = RuntimeMetadataGenerator(
        runtime_dir=tmp_path,
        commit=COMMIT,
        short_commit=COMMIT[:12],
        created_at="2026-07-16T13:18:00Z",
    )

    with pytest.raises(FileExistsError, match="already exists"):
        generator.write()

    assert metadata_path.read_text(encoding="utf-8") == "existing"
    assert not (tmp_path / ".aicontrolcenter-source-commit").exists()


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

    assert not (tmp_path / "metadata.json").exists()
    assert not (tmp_path / ".aicontrolcenter-source-commit").exists()


@pytest.mark.parametrize(
    "commit",
    [
        COMMIT[:39],
        COMMIT.upper(),
        "g" * 40,
    ],
)
def test_runtime_metadata_generator_fails_closed_for_invalid_commits(
    tmp_path: Path,
    commit: str,
) -> None:
    generator = RuntimeMetadataGenerator(
        runtime_dir=tmp_path,
        commit=commit,
        short_commit=commit[:12],
        created_at="2026-07-16T13:18:00Z",
    )

    with pytest.raises(ValueError, match="commit"):
        generator.write()

    assert list(tmp_path.iterdir()) == []


def test_runtime_metadata_generator_cleans_partial_contract_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_replace = os.replace
    replacements = 0

    def fail_second_replace(source: Path, destination: Path) -> None:
        nonlocal replacements
        replacements += 1
        if replacements == 2:
            raise OSError("simulated metadata replacement failure")
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_second_replace)
    generator = RuntimeMetadataGenerator(
        runtime_dir=tmp_path,
        commit=COMMIT,
        short_commit=COMMIT[:12],
        created_at="2026-07-16T13:18:00Z",
    )

    with pytest.raises(OSError, match="simulated"):
        generator.write()

    assert list(tmp_path.iterdir()) == []


def test_runtime_metadata_generator_rejects_short_commit_mismatch(
    tmp_path: Path,
) -> None:
    generator = RuntimeMetadataGenerator(
        runtime_dir=tmp_path,
        commit=COMMIT,
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
