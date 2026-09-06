from __future__ import annotations

import socket
from collections.abc import Mapping

import httpx
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from sys4ai_memory.contracts import ErrorCategory, OperationName
from sys4ai_memory.interfaces import (
    HTTP_OPERATION_PATHS,
    InterfaceIdentity,
    TestOnlyLoopbackNoAuth,
    create_http_app,
)
from sys4ai_memory.security import DeploymentMode
from tests.interfaces.helpers import (
    IDENTITY,
    REQUEST_ID,
    TRACE_ID,
    RecordingDispatcher,
    StaticAuthenticator,
)


def _body(
    *, project_id: str = "project-alpha", dataset_id: str = "dataset-alpha"
) -> dict[str, object]:
    return {
        "dataset_id": dataset_id,
        "scope": {
            "level": "project",
            "scope_id": project_id,
            "parent_scopes": [],
        },
        "query_project_ids": [project_id],
        "explicit_cross_project": False,
        "client_id": "http-test",
        "purpose": "HTTP adapter test",
        "request_id": REQUEST_ID,
        "trace_id": TRACE_ID,
        "idempotency_key": None,
        "payload": {"detailed": False},
    }


def test_http_app_creation_fails_closed_without_authentication() -> None:
    dispatcher = RecordingDispatcher()

    with pytest.raises(ValueError, match="authentication is required"):
        create_http_app(dispatcher)
    with pytest.raises(ValueError, match="prohibited for shared"):
        create_http_app(
            dispatcher,
            deployment_mode=DeploymentMode.SHARED,
            test_only_no_auth=TestOnlyLoopbackNoAuth(
                identity=IDENTITY,
                project_id="project-alpha",
                dataset_id="dataset-alpha",
            ),
        )


def test_http_app_declares_all_public_routes_without_opening_a_listener(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def prohibit_socket(*args: object, **kwargs: object) -> None:
        nonlocal calls
        del args, kwargs
        calls += 1
        raise AssertionError("network sockets are prohibited in interface tests")

    monkeypatch.setattr(socket, "socket", prohibit_socket)
    app = create_http_app(
        RecordingDispatcher(),
        authenticator=StaticAuthenticator(IDENTITY),
    )

    route_methods = {
        route.name: route.methods
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.name in {action.value for action in HTTP_OPERATION_PATHS}
    }
    assert len(route_methods) == len(OperationName) + 1
    assert all(methods == {"POST"} for methods in route_methods.values())
    assert app.state.network_listener_started is False
    assert calls == 0


def test_authenticated_http_dispatches_in_process_with_trace_identity() -> None:
    dispatcher = RecordingDispatcher()
    authenticator = StaticAuthenticator(IDENTITY)
    app = create_http_app(dispatcher, authenticator=authenticator)

    response = TestClient(app).post(
        "/v1/projects/project-alpha/health",
        json=_body(),
    )

    assert response.status_code == 200
    assert response.json()["request_id"] == REQUEST_ID
    assert response.json()["trace_id"] == TRACE_ID
    assert authenticator.calls == 1
    assert dispatcher.requests[0].authorization.identity == IDENTITY


def test_http_project_scope_mismatch_is_denied_before_dispatch() -> None:
    dispatcher = RecordingDispatcher()
    app = create_http_app(dispatcher, authenticator=StaticAuthenticator(IDENTITY))

    response = TestClient(app).post(
        "/v1/projects/project-beta/health",
        json=_body(project_id="project-alpha"),
    )

    assert response.status_code == 403
    assert response.json()["error"]["category"] == ErrorCategory.AUTHORITY_VIOLATION.value
    assert not dispatcher.requests


def test_http_authentication_failure_is_safe_and_fail_closed() -> None:
    class FailingAuthenticator:
        def authenticate(self, headers: Mapping[str, str]) -> InterfaceIdentity:
            del headers
            raise RuntimeError("authorization: Bearer do-not-return")

    dispatcher = RecordingDispatcher()
    app = create_http_app(dispatcher, authenticator=FailingAuthenticator())

    response = TestClient(app).post(
        "/v1/projects/project-alpha/health",
        json=_body(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["category"] == ErrorCategory.PERMISSION_DENIED.value
    assert "do-not-return" not in response.text
    assert not dispatcher.requests


@pytest.mark.asyncio
async def test_explicit_test_only_no_auth_accepts_loopback_and_rejects_non_loopback() -> None:
    dispatcher = RecordingDispatcher()
    app = create_http_app(
        dispatcher,
        deployment_mode=DeploymentMode.SINGLE_USER_DEVELOPMENT,
        test_only_no_auth=TestOnlyLoopbackNoAuth(
            identity=IDENTITY,
            project_id="project-alpha",
            dataset_id="dataset-alpha",
        ),
    )
    assert app.state.security_label.startswith("TEST ONLY")

    loopback_transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 41000))
    async with httpx.AsyncClient(transport=loopback_transport, base_url="http://local") as client:
        allowed = await client.post("/v1/projects/project-alpha/health", json=_body())
    remote_transport = httpx.ASGITransport(app=app, client=("192.0.2.10", 41000))
    async with httpx.AsyncClient(transport=remote_transport, base_url="http://local") as client:
        denied = await client.post("/v1/projects/project-alpha/health", json=_body())

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert len(dispatcher.requests) == 1


def test_http_validation_error_does_not_echo_invalid_input() -> None:
    dispatcher = RecordingDispatcher()
    app = create_http_app(dispatcher, authenticator=StaticAuthenticator(IDENTITY))
    body = _body()
    body["dataset_id"] = "password=do-not-return"

    response = TestClient(app).post("/v1/projects/project-alpha/health", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["category"] == ErrorCategory.SCHEMA_INVALID.value
    assert "do-not-return" not in response.text
    assert not dispatcher.requests


def test_http_long_operation_returns_retry_status_and_202() -> None:
    dispatcher = RecordingDispatcher()
    app = create_http_app(dispatcher, authenticator=StaticAuthenticator(IDENTITY))
    body = _body()
    body["idempotency_key"] = "sync-retry-key"
    body["payload"] = {"source_ids": [], "full": False, "dry_run": True}

    response = TestClient(app).post("/v1/projects/project-alpha/sync", json=body)

    assert response.status_code == 202
    status = response.json()["operation_status"]
    assert status["retry_safe"] is True
    assert status["status_action"] == "memory.operations.status"
