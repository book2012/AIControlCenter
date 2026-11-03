import asyncio
from hashlib import sha256
from pathlib import Path
import sqlite3
import importlib

from fastapi import FastAPI
import httpx
import pytest
pytest.importorskip("aicc_plugin_shopping", reason="optional shopping storage package required")
from aicc_plugin_shopping.inquiries import SQLiteInquiryRepository, InMemoryInquiryRepository
from aicc_plugin_shopping.customer_persistence import PersistenceError
from aicc_plugin_shopping.storage_resource import ShoppingStorageResource
from aicc_plugin_shopping.models import Product
from decimal import Decimal
from core.modules.shopping_storage import storage_module_instance
from core.modules.lifecycle import create_managed_app


def provision(tmp_path):
    path = tmp_path / 'shopping.db'
    SQLiteInquiryRepository(str(path)).initialize_persistence_schema(str(path))
    return path


def product():
    return Product('fixture', 'Synthetic fixture', 'fixture', '', Decimal('19.00'), 'KRW', 'fixture', True, 'fixture')


def test_existing_store_attachment_never_migrates_and_defaults_no_contacts(tmp_path):
    path = provision(tmp_path)
    before = sha256(path.read_bytes()).hexdigest()
    resource = ShoppingStorageResource(path, data_root=tmp_path)
    assert not resource.ready
    resource.start()
    assert resource.ready and resource.inquiries.list() == []
    resource.close()
    resource.close()
    assert not resource.ready
    assert path.exists() and sha256(path.read_bytes()).hexdigest() == before
    memory = InMemoryInquiryRepository()
    assert memory.create(product(), None, 'fixture').contact_channels == []


def test_missing_invalid_and_outside_store_fail_without_creating_or_altering(tmp_path):
    root = tmp_path / 'owned'
    root.mkdir()
    missing = root / 'missing.db'
    with pytest.raises(PersistenceError):
        ShoppingStorageResource(missing, data_root=root).start()
    assert not missing.exists()
    path = provision(tmp_path)
    with pytest.raises(PersistenceError):
        ShoppingStorageResource(path, data_root=root).start()
    empty = root / 'invalid.db'
    empty.write_bytes(b'')
    with pytest.raises((PersistenceError, sqlite3.Error)):
        ShoppingStorageResource(empty, data_root=root).start()
    assert empty.read_bytes() == b''
    link = root / 'link.db'
    link.symlink_to(path)
    with pytest.raises(PersistenceError):
        ShoppingStorageResource(link, data_root=root).start()


def test_legacy_repository_inheritance_and_contact_configuration_are_preserved(monkeypatch, tmp_path):
    import core.shopping.inquiries as legacy
    from aicc_plugin_shopping.inquiries import InquirySessionAuthority as moved
    assert legacy.InquirySessionAuthority is moved
    contacts = [{'type': 'fixture', 'label': 'Synthetic', 'url': 'https://fixture.invalid'}]
    monkeypatch.setattr(legacy, 'configured_contact_channels', lambda: contacts)
    repo = legacy.SQLiteInquiryRepository(str(tmp_path / 'legacy.db'))
    assert isinstance(repo, legacy.InMemoryInquiryRepository)
    response = repo.create(product(), None, 'fixture')
    assert response.contact_channels == contacts
    response.contact_channels[0]['label'] = 'changed'
    assert contacts[0]['label'] == 'Synthetic'


@pytest.mark.parametrize('name', ['customer_identity', 'customer_sessions', 'customer_auth',
    'customer_persistence', 'customer_session_service', 'migration_contract'])
def test_security_domain_module_identity_is_preserved(name):
    assert importlib.import_module('core.shopping.' + name) is importlib.import_module('aicc_plugin_shopping.' + name)


def test_drain_persists_leased_job_result_and_reattach_reuses_existing_data(tmp_path):
    path = provision(tmp_path)
    async def scenario():
        resources = []
        entered, release = asyncio.Event(), asyncio.Event()
        def app_factory(resource):
            resources.append(resource)
            app = FastAPI()
            @app.get('/status')
            def status():
                return {'ready': resource.ready}
            return app
        def factory():
            return storage_module_instance(path, data_root=tmp_path, application_factory=app_factory)
        app = create_managed_app(['shopping'], providers={'shopping': factory})
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
                manager = app.state.module_manager
                assert (await client.get('/extensions/shopping/status')).json() == {'ready': True}
                async def work():
                    async with manager.lease('shopping'):
                        entered.set()
                        await release.wait()
                        return resources[-1].inquiries.create(product(), None, 'retained fixture')
                task = asyncio.create_task(work())
                await entered.wait()
                detached = asyncio.create_task(manager.detach('shopping'))
                await asyncio.sleep(0)
                assert resources[0].ready
                assert (await client.get('/extensions/shopping/status')).status_code == 503
                release.set()
                created = await task
                await detached
                assert not resources[0].ready
                assert path.exists()
                assert (await client.get('/extensions/shopping/status')).status_code == 404
                await manager.attach('shopping')
                assert resources[-1].ready
                assert resources[-1].inquiries.get(created.id).formatted_message.endswith('retained fixture')
                assert (await client.get('/health')).status_code == 200
        assert all(not r.ready for r in resources)
    asyncio.run(scenario())


def test_failed_application_construction_closes_storage_and_keeps_core_available(tmp_path):
    path = provision(tmp_path)
    resources = []
    def broken(resource):
        resources.append(resource)
        raise RuntimeError('fixture-private-detail')
    async def scenario():
        app = create_managed_app(['shopping'], providers={'shopping': lambda: storage_module_instance(
            path, data_root=tmp_path, application_factory=broken)})
        async with app.router.lifespan_context(app):
            assert app.state.module_manager.slots['shopping'].state == 'UNAVAILABLE'
            assert resources and not resources[0].ready
            assert path.exists()
    asyncio.run(scenario())


def test_isolated_backup_restore_preserves_fixture_data_without_attach_migration(tmp_path):
    source = provision(tmp_path)
    resource = ShoppingStorageResource(source, data_root=tmp_path)
    resource.start()
    created = resource.inquiries.create(product(), None, 'backup fixture')
    restored = tmp_path / 'restored.db'
    with sqlite3.connect(source) as origin, sqlite3.connect(restored) as target:
        origin.backup(target)
        assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    resource.close()
    before = sha256(restored.read_bytes()).hexdigest()
    recovered = ShoppingStorageResource(restored, data_root=tmp_path)
    recovered.start()
    assert recovered.inquiries.get(created.id).formatted_message.endswith('backup fixture')
    recovered.close()
    assert sha256(restored.read_bytes()).hexdigest() == before
    assert source.exists()
