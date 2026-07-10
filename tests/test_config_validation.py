from core.runtime.config_validation import ConfigValidation


def test_config_validation_shape():
    result = ConfigValidation().validate()

    assert "valid" in result
    assert "items" in result
    assert "OPENAI_API_KEY" in result["items"]
