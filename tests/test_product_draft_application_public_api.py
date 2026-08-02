"""Public-package smoke coverage for the SHOP-02C application boundary."""

from core.shopping.product_drafts import application


def test_product_draft_application_public_api_is_explicit() -> None:
    assert tuple(application.__all__) == tuple(sorted(application.__all__))
    assert "ProductDraftValidationService" in application.__all__
    assert "ProductDraftReviewService" in application.__all__
