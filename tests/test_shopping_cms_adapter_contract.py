from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from core.shopping.adapters.cms_contract import (
    CmsAdapterContractError,
    EXPECTED_RETURN_CONTRACTS,
    cms_contract_manifest,
    validate_cms_adapter_class,
    validate_cms_adapter_instance,
)
from core.shopping.contracts.provisional import (
    ContentSnapshot,
    ContentSnapshotPage,
)


class GoodCmsAdapter:
    async def get_content(self, *, context, content_id) -> ContentSnapshot:
        return {}

    async def list_content(self, *, context, page) -> ContentSnapshotPage:
        return {}



def test_manifest_has_exact_capability_bindings():
    manifest = cms_contract_manifest()

    assert manifest["methods"] == {
        "get_content": {
            "capability_id": (
                "shopping.content.get"
            ),
            "return_contract": (
                "ContentSnapshot"
            ),
        },
        "list_content": {
            "capability_id": (
                "shopping.content.list"
            ),
            "return_contract": (
                "ContentSnapshotPage"
            ),
        },
    }


def test_manifest_is_json_serializable_and_read_only():
    manifest = cms_contract_manifest()

    assert json.dumps(
        manifest,
        sort_keys=True,
    )

    assert manifest["read_only"] is True
    assert (
        manifest[
            "write_methods_allowed"
        ]
        is False
    )
    assert (
        manifest[
            "vendor_dto_escape_allowed"
        ]
        is False
    )


def test_valid_adapter_class_passes():
    assert (
        validate_cms_adapter_class(
            GoodCmsAdapter
        )
        is GoodCmsAdapter
    )


def test_valid_adapter_instance_passes():
    adapter = GoodCmsAdapter()

    assert (
        validate_cms_adapter_instance(
            adapter
        )
        is adapter
    )


def test_missing_required_method_is_rejected():
    class MissingAdapter(
        GoodCmsAdapter
    ):
        get_content = None

    with pytest.raises(
        CmsAdapterContractError
    ):
        validate_cms_adapter_class(
            MissingAdapter
        )


def test_sync_required_method_is_rejected():
    class SyncAdapter(
        GoodCmsAdapter
    ):
        def get_content(
            self,
            **kwargs,
        ) -> ContentSnapshot:
            return {}

    with pytest.raises(
        CmsAdapterContractError
    ):
        validate_cms_adapter_class(
            SyncAdapter
        )


def test_wrong_signature_is_rejected():
    class WrongSignatureAdapter(
        GoodCmsAdapter
    ):
        async def get_content(
            self,
            unexpected,
        ) -> ContentSnapshot:
            return {}

    with pytest.raises(
        CmsAdapterContractError
    ):
        validate_cms_adapter_class(
            WrongSignatureAdapter
        )


def test_write_like_public_method_is_rejected():
    class WriteAdapter(
        GoodCmsAdapter
    ):
        async def publish_content(
            self,
        ):
            return None

    with pytest.raises(
        CmsAdapterContractError
    ):
        validate_cms_adapter_class(
            WriteAdapter
        )


def test_return_contract_mapping_is_immutable():
    with pytest.raises(
        TypeError
    ):
        EXPECTED_RETURN_CONTRACTS[
            "get_content"
        ] = "WordPressPost"


def test_contract_module_has_no_network_or_environment_imports():
    path = Path(
        "core/shopping/adapters/cms_contract.py"
    )

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }

    imported = set()

    for node in ast.walk(tree):
        if isinstance(
            node,
            ast.Import,
        ):
            for item in node.names:
                imported.add(
                    item.name.split(
                        "."
                    )[0]
                )

        elif (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and node.module
        ):
            imported.add(
                node.module.split(
                    "."
                )[0]
            )

    assert not (
        imported
        & forbidden
    )
