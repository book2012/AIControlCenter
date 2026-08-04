from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "ops"
    / "macos"
    / "runtime"
    / "bootstrap-production-runtime.sh"
)

def test_bootstrap_generates_runtime_metadata_before_switch() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    metadata_step = content.index(
        'CURRENT_STEP="generate runtime metadata"'
    )
    switch_step = content.index(
        'CURRENT_STEP="activate runtime"'
    )

    assert metadata_step < switch_step

def test_bootstrap_validates_metadata_before_switch() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    assert "RuntimeMetadataGenerator" in content
    assert "RuntimeMetadata" in content
    assert 'metadata["available"] is not True' in content


def test_bootstrap_generator_owns_source_commit_marker() -> None:
    generator = (
        ROOT / "core" / "runtime" / "metadata_generator.py"
    ).read_text(encoding="utf-8")

    assert (
        'marker_path = runtime_dir / ".aicontrolcenter-source-commit"'
        in generator
    )
    assert 'marker = f"{self.commit}\\n"' in generator

    content = SCRIPT.read_text(encoding="utf-8")
    marker_validation = content.index(
        "marker_path.read_bytes() != expected_marker"
    )
    activation_step = content.index(
        'CURRENT_STEP="activate runtime"'
    )
    assert marker_validation < activation_step

def test_bootstrap_uses_fail_closed_error_handling() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    assert "set -Eeuo pipefail" in content
    assert "trap 'handle_error $?' ERR" in content

def test_metadata_validation_precedes_symlink_activation() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    metadata_validation = content.index(
        'if metadata["available"] is not True:'
    )
    activation_step = content.index(
        'CURRENT_STEP="activate runtime"'
    )
    symlink_switch = content.index("ln -sfn")

    assert metadata_validation < activation_step
    assert activation_step < symlink_switch
