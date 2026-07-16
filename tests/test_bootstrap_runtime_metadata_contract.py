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
