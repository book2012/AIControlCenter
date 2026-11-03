import asyncio
from pathlib import Path

from fastapi import FastAPI
import httpx
import pytest

from core.modules.composition import ModuleDescriptor, ModuleConfigurationError
from core.modules.lifecycle import (
    ModuleManager, ModuleInstance, LifecycleDenied, DrainTimeout, create_managed_app,
)
from core.api.modular import create_managed_validation_app


def run(coroutine):
    return asyncio.run(coroutine)


def provider():
    app = FastAPI()
    @app.get("/health")
    def health():
        return {"ok": True}
    return app


def test_attach_detach_reattach_closes_once_per_generation(tmp_path):
    async def scenario():
        events = []
        data = tmp_path / "owned-data"
        data.write_text("retain")
        def factory():
            return ModuleInstance(provider(), lambda: events.append("open"), lambda: events.append("close"))
        manager = ModuleManager({"shopping": factory})
        await manager.attach("shopping")
        await manager.attach("shopping")
        async with manager.lease("shopping"):
            assert manager.slots["shopping"].active == 1
        await manager.detach("shopping")
        await manager.detach("shopping")
        await manager.attach("shopping")
        await manager.detach("shopping")
        assert events == ["open", "close", "open", "close"]
        assert data.read_text() == "retain"
    run(scenario())


def test_drain_blocks_new_work_and_retains_resources_until_last_lease():
    async def scenario():
        entered, release, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()
        manager = ModuleManager({"shopping": lambda: ModuleInstance(provider(), close=closed.set)})
        await manager.attach("shopping")
        async def work():
            async with manager.lease("shopping"):
                entered.set()
                await release.wait()
        task = asyncio.create_task(work())
        await entered.wait()
        detaching = asyncio.create_task(manager.detach("shopping"))
        await asyncio.sleep(0)
        assert manager.slots["shopping"].state == "DRAINING"
        assert not closed.is_set()
        with pytest.raises(LifecycleDenied):
            async with manager.lease("shopping"):
                pytest.fail("new work admitted")
        release.set()
        await task
        await detaching
        assert closed.is_set()
        assert manager.slots["shopping"].state == "DETACHED"
    run(scenario())


def test_timeout_does_not_close_active_resources_or_allow_reattach():
    async def scenario():
        closed = []
        manager = ModuleManager({"shopping": lambda: ModuleInstance(provider(), close=lambda: closed.append(1))})
        await manager.attach("shopping")
        async with manager.lease("shopping"):
            with pytest.raises(DrainTimeout):
                await manager.detach("shopping", timeout=0.01)
            assert manager.slots["shopping"].state == "DRAINING"
            assert closed == []
            with pytest.raises(LifecycleDenied):
                await manager.attach("shopping")
        await manager.detach("shopping")
        assert closed == [1]
    run(scenario())


def test_cancelled_work_releases_lease():
    async def scenario():
        entered = asyncio.Event()
        manager = ModuleManager({"shopping": provider})
        await manager.attach("shopping")
        async def work():
            async with manager.lease("shopping"):
                entered.set()
                await asyncio.Event().wait()
        task = asyncio.create_task(work())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert manager.slots["shopping"].active == 0
        await manager.detach("shopping")
    run(scenario())


def test_start_failure_cleans_resources_and_isolates_other_modules():
    async def scenario():
        closed = []
        def fail():
            raise RuntimeError("secret must never be projected")
        manager = ModuleManager({"shopping": lambda: ModuleInstance(provider(), fail, lambda: closed.append(1)),
                                 "personal-assistant": provider})
        await manager.attach("shopping")
        await manager.attach("personal-assistant")
        assert manager.slots["shopping"].state == "UNAVAILABLE"
        assert manager.slots["personal-assistant"].state == "ATTACHED"
        assert closed == [1]
        assert "secret" not in str(manager.snapshot())
        await manager.detach("personal-assistant")
    run(scenario())


def test_failed_cleanup_requires_explicit_recovery_before_reattach():
    async def scenario():
        attempts = []
        def close():
            attempts.append(1)
            if len(attempts) == 1:
                raise RuntimeError("private path")
        manager = ModuleManager({"shopping": lambda: ModuleInstance(provider(), close=close)})
        await manager.attach("shopping")
        with pytest.raises(LifecycleDenied, match="module_cleanup_failed"):
            await manager.detach("shopping")
        assert manager.slots["shopping"].state == "STOP_FAILED"
        with pytest.raises(LifecycleDenied):
            await manager.attach("shopping")
        await manager.detach("shopping")
        assert manager.slots["shopping"].state == "DETACHED"
        assert len(attempts) == 2
    run(scenario())


def test_dependent_prevents_unsafe_parent_detach():
    async def scenario():
        descriptors = (ModuleDescriptor("parent"), ModuleDescriptor("child", ("parent",)))
        manager = ModuleManager({"parent": provider, "child": provider}, descriptors=descriptors)
        await manager.attach("child")
        assert manager.slots["child"].state == "BLOCKED"
        await manager.attach("parent")
        await manager.attach("child")
        with pytest.raises(LifecycleDenied, match="attached_dependents_exist"):
            await manager.detach("parent")
        await manager.detach("child")
        await manager.detach("parent")
    run(scenario())


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf"), "1"])
def test_invalid_deadlines_rejected(timeout):
    async def scenario():
        with pytest.raises(ValueError):
            await ModuleManager().detach("shopping", timeout=timeout)
    run(scenario())


def test_managed_http_and_other_modules_survive_drain_and_reattach():
    async def scenario():
        entered, release, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()
        async def factory():
            app = provider()
            @app.get("/slow")
            async def slow():
                entered.set()
                await release.wait()
                return {"completed": True}
            return ModuleInstance(app, close=closed.set)
        app = create_managed_app(["shopping", "personal-assistant"],
            providers={"shopping": factory, "personal-assistant": provider})
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                manager = app.state.module_manager
                task = asyncio.create_task(client.get("/extensions/shopping/slow"))
                await entered.wait()
                detach = asyncio.create_task(manager.detach("shopping"))
                await asyncio.sleep(0)
                assert (await client.get("/extensions/shopping/health")).status_code == 503
                assert (await client.get("/health")).status_code == 200
                assert (await client.get("/extensions/personal-assistant/health")).status_code == 200
                assert not closed.is_set()
                release.set()
                assert (await task).json() == {"completed": True}
                await detach
                assert closed.is_set()
                assert (await client.get("/extensions/shopping/health")).status_code == 404
                await manager.attach("shopping")
                assert (await client.get("/extensions/shopping/health")).status_code == 200
                assert (await client.post("/extensions/shopping/orders")).status_code == 405
                assert (await client.post("/platform/modules")).status_code == 405
    run(scenario())


def test_real_service_adapters_do_not_claim_live_authority(monkeypatch):
    import socket
    import sqlite3
    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected live access")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    async def scenario():
        path = Path(__file__).resolve().parents[1] / "config/modules/all-adapters.json"
        app = create_managed_validation_app(manifest_path=path)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                statuses = (await client.get("/platform/modules")).json()["modules"]
                assert all(x["state"] == "ATTACHED" for x in statuses)
                note = (await client.get("/extensions/creative-notes/connection")).json()
                assert note["private_notes_access"] is False
                assistant = (await client.get("/extensions/personal-assistant/connection")).json()
                assert assistant["execution_enabled"] is False
                assert (await client.get("/extensions/shopping/products")).status_code == 200
                for name in ["shopping", "creative-notes", "personal-assistant"]:
                    await app.state.module_manager.detach(name)
                    assert (await client.get("/extensions/" + name + "/health")).status_code == 404
        assert all(x["state"] == "DETACHED" for x in app.state.module_manager.snapshot())
    run(scenario())


def test_cancelled_attachment_closes_partial_resource():
    async def scenario():
        entered, closed = asyncio.Event(), asyncio.Event()
        async def start():
            entered.set()
            await asyncio.Event().wait()
        manager = ModuleManager({"shopping": lambda: ModuleInstance(provider(), start, closed.set)})
        task = asyncio.create_task(manager.attach("shopping"))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed.is_set()
        assert manager.slots["shopping"].state == "UNAVAILABLE"
        assert manager.slots["shopping"].instance is None
    run(scenario())


def test_cancelled_detach_does_not_reopen_admission():
    async def scenario():
        manager = ModuleManager({"shopping": provider})
        await manager.attach("shopping")
        async with manager.lease("shopping"):
            task = asyncio.create_task(manager.detach("shopping"))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert manager.slots["shopping"].state == "DRAINING"
            with pytest.raises(LifecycleDenied):
                async with manager.lease("shopping"):
                    pass
        await manager.detach("shopping")
        assert manager.slots["shopping"].state == "DETACHED"
    run(scenario())


def test_async_concurrent_attach_constructs_one_instance():
    async def scenario():
        calls = []
        async def factory():
            calls.append(1)
            await asyncio.sleep(0)
            return provider()
        manager = ModuleManager({"shopping": factory})
        await asyncio.gather(manager.attach("shopping"), manager.attach("shopping"))
        assert calls == [1]
        await manager.detach("shopping")
    run(scenario())


def test_new_module_core_has_no_outer_imports_at_any_indentation():
    import ast
    root = Path(__file__).resolve().parents[1]
    paths = list((root / "core/modules").glob("*.py")) + [root / "core/api/modular.py"]
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text())):
            names = ([x.name for x in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            assert not any(n.split(".")[0] in {"ops", "integrations"} for n in names), path


def test_outer_composition_reuses_openclaw_without_live_access():
    from integrations.module_composition import create_validation_app
    from fastapi.testclient import TestClient
    path = Path(__file__).resolve().parents[1] / "config/modules/all-adapters.json"
    with TestClient(create_validation_app(manifest_path=path)) as client:
        response = client.get("/extensions/personal-assistant/health")
        assert response.status_code == 200
        assert 'NOT_DEPLOYED' in response.text
