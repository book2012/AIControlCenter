from collections import Counter

from fastapi.routing import APIRoute

from core.api.app import app


def test_api_routes_are_unique():
    route_keys = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        methods = tuple(sorted(route.methods or []))
        route_keys.append((route.path, methods))

    counts = Counter(route_keys)
    duplicates = {
        key: count
        for key, count in counts.items()
        if count > 1
    }

    assert duplicates == {}


def test_openapi_operation_ids_are_unique():
    schema = app.openapi()

    operation_ids = []

    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")

            if operation_id:
                operation_ids.append(operation_id)

    counts = Counter(operation_ids)
    duplicates = {
        operation_id: count
        for operation_id, count in counts.items()
        if count > 1
    }

    assert duplicates == {}
