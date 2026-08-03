from pathlib import Path

from core.shopping.product_drafts.deployment import FakeCommerceProductWriteAdapter


def test_product_draft_live_write_contracts_and_routes_remain_unchanged():
    assert '"const":"1.0.0"' in Path("docs/contracts/shopping/v1/deployment-intent.schema.json").read_text().replace(" ", "")
    assert '"const": "1.0.0"' in Path("docs/contracts/shopping/v1/product-draft.schema.json").read_text()
    assert not any("mutation" in path.name.lower() for path in Path("core/api").rglob("*.py"))


def test_product_draft_live_write_shop_03a_fake_adapter_public_compatibility():
    adapter = FakeCommerceProductWriteAdapter()
    assert adapter.calls == ()
