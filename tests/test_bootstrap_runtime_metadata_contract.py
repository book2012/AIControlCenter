from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/macos/runtime/bootstrap-production-runtime.sh"


def test_bootstrap_generates_and_validates_metadata_before_finalization() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.index("generate_runtime_metadata") < content.index(
        "finalize_runtime"
    )
    assert 'validate_runtime "$STAGING_PATH" "$GIT_COMMIT"' in content
    assert "RuntimeMetadataGenerator" in content
    assert "RuntimeMetadata" in content
    assert 'metadata["available"] is not True' in content


def test_bootstrap_generator_owns_exact_source_commit_marker() -> None:
    generator = (ROOT / "core/runtime/metadata_generator.py").read_text(
        encoding="utf-8"
    )
    assert 'marker_path = runtime_dir / ".aicontrolcenter-source-commit"' in generator
    assert 'marker = f"{self.commit}\\n"' in generator

    content = SCRIPT.read_text(encoding="utf-8")
    assert 'expected_marker = (expected_commit + "\\n").encode("ascii")' in content
    assert "if marker != expected_marker:" in content


def test_bootstrap_uses_fail_closed_error_handling() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in content
    assert "trap 'handle_error $?' ERR" in content


def test_activation_is_separate_and_atomic() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "activate_runtime()" in content
    assert 'ln -s "$VENV_PATH" "$temporary_link"' in content
    assert 'mv -f -h "$temporary_link" "$RUNTIME_ROOT/current"' in content
    assert "ln -sfn" not in content
