from datetime import timedelta

from test_shop_03a_controlled_write_architecture import (NOW, allow, approved_pair,
                                                        service)
from core.shopping.product_drafts.deployment import (DeploymentOutcome,
    SourceFreshnessPolicy)


def execute(app, revision, intent):
    return app.execute(revision, intent,
        freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)),
        evaluated_at=NOW, completed_at=NOW)


def test_product_draft_deployment_idempotent_replay_does_not_call_adapter_twice():
    revision, intent = approved_pair()
    app, writer = service(intent, (allow(intent),))
    assert execute(app, revision, intent).outcome is DeploymentOutcome.FAKE_APPLIED
    assert execute(app, revision, intent).outcome is DeploymentOutcome.IDEMPOTENT_REPLAY
    assert len(writer.calls) == 1


def test_product_draft_deployment_key_reuse_conflict():
    revision, intent = approved_pair()
    app, writer = service(intent, (allow(intent),))
    execute(app, revision, intent)
    later = NOW + timedelta(seconds=1)
    app._authorization = type(app._authorization)((allow(intent, evaluated_at=later),))
    result = app.execute(revision, intent,
        freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)),
        evaluated_at=later, completed_at=later)
    assert result.outcome is DeploymentOutcome.IDEMPOTENCY_CONFLICT
    assert len(writer.calls) == 1


def test_product_draft_deployment_denied_attempt_cannot_replay_as_successful():
    revision, intent = approved_pair()
    app, writer = service(intent)
    assert execute(app, revision, intent).outcome is DeploymentOutcome.REJECTED_AUTHORIZATION
    app._authorization = type(app._authorization)((allow(intent),))
    assert execute(app, revision, intent).outcome is DeploymentOutcome.FAKE_APPLIED
    assert len(writer.calls) == 1


def test_product_draft_deployment_package_has_no_runtime_io_dependencies():
    import ast
    from pathlib import Path
    package = Path("core/shopping/product_drafts/deployment")
    forbidden = {"fastapi", "requests", "httpx", "aiohttp", "socket", "sqlite3", "pathlib", "subprocess"}
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imports |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not imports & forbidden
