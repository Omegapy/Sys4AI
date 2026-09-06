"""FastAPI adapter that never owns or starts a network listener."""

from __future__ import annotations

import ipaddress
from collections.abc import Callable, Coroutine, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, JsonValue, ValidationError

from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    ErrorCategory,
    OperationName,
    ScopeReference,
)
from sys4ai_memory.contracts._base import (
    ApiVersion,
    ContractModel,
    NonEmptyString,
    RequestId,
    SchemaVersion,
    StableIdentifier,
    TraceId,
)
from sys4ai_memory.security import DeploymentMode

from .common import invoke_dispatcher, project_authorization, safe_trace_id
from .dispatcher import MemoryServiceDispatcher, error_envelope
from .models import (
    ControlAction,
    DispatchResponse,
    DispatchSuccess,
    InterfaceAction,
    InterfaceIdentity,
    InterfaceKind,
)


class HttpAuthenticator(Protocol):
    """Resolve trusted identity from transport metadata without exposing credentials."""

    def authenticate(self, headers: Mapping[str, str]) -> InterfaceIdentity: ...


@dataclass(frozen=True, slots=True)
class TestOnlyLoopbackNoAuth:
    """Explicit non-shared posture for ASGI tests and loopback development only."""

    __test__: ClassVar[bool] = False
    identity: InterfaceIdentity
    project_id: str
    dataset_id: str

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.dataset_id.strip():
            raise ValueError("test-only project and dataset identities must not be blank")

    @property
    def security_label(self) -> str:
        return "TEST ONLY: loopback single-user mode; not a secure shared configuration"


class HttpInvocation(ContractModel):
    """Transport fields accepted after the operation is selected by the route."""

    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    dataset_id: StableIdentifier
    scope: ScopeReference
    query_project_ids: tuple[StableIdentifier, ...] = Field(min_length=1)
    explicit_cross_project: bool = False
    client_id: StableIdentifier = "sys4ai-http-client"
    purpose: NonEmptyString = "memory HTTP operation"
    request_id: RequestId | None = None
    trace_id: TraceId | None = None
    idempotency_key: str | None = None
    payload: dict[str, JsonValue]


HTTP_OPERATION_PATHS: dict[InterfaceAction, str] = {
    OperationName.HEALTH: "/v1/projects/{project_id}/health",
    OperationName.SOURCES_LIST: "/v1/projects/{project_id}/sources/list",
    OperationName.SOURCES_EXPLAIN: "/v1/projects/{project_id}/sources/explain",
    OperationName.SYNC: "/v1/projects/{project_id}/sync",
    OperationName.RECALL: "/v1/projects/{project_id}/recall",
    OperationName.GET: "/v1/projects/{project_id}/records/get",
    OperationName.GRAPH: "/v1/projects/{project_id}/graph",
    OperationName.PROPOSE: "/v1/projects/{project_id}/proposals/propose",
    OperationName.APPROVE: "/v1/projects/{project_id}/proposals/approve",
    OperationName.SUPERSEDE: "/v1/projects/{project_id}/records/supersede",
    OperationName.IMPROVE: "/v1/projects/{project_id}/improve",
    OperationName.FORGET: "/v1/projects/{project_id}/forget",
    OperationName.REBUILD: "/v1/projects/{project_id}/rebuild",
    OperationName.EXPORT: "/v1/projects/{project_id}/export",
    OperationName.IMPORT: "/v1/projects/{project_id}/import",
    OperationName.EXPLAIN: "/v1/projects/{project_id}/explain",
    ControlAction.OPERATION_STATUS: "/v1/projects/{project_id}/operations/status",
}


def _http_status(response: DispatchResponse) -> int:
    if isinstance(response, DispatchSuccess):
        if response.operation_status is not None and response.operation_status.state.value in {
            "pending",
            "running",
            "cancel_requested",
        }:
            return 202
        return 200
    category = response.error.category
    if category is ErrorCategory.SCHEMA_INVALID:
        return 422
    if category is ErrorCategory.PERMISSION_DENIED:
        return 403
    if category in {
        ErrorCategory.PROJECT_NOT_FOUND,
        ErrorCategory.SOURCE_NOT_REGISTERED,
    }:
        return 404
    if category in {ErrorCategory.CONFLICT_DETECTED, ErrorCategory.CONCURRENT_OPERATION}:
        return 409
    if category in {ErrorCategory.PROVIDER_UNAVAILABLE, ErrorCategory.MEMORY_NOT_INITIALIZED}:
        return 503
    return 400


def _json_response(response: DispatchResponse, *, status_code: int | None = None) -> JSONResponse:
    return JSONResponse(
        response.model_dump(mode="json", exclude_none=False),
        status_code=_http_status(response) if status_code is None else status_code,
    )


def _is_loopback(request: Request) -> bool:
    if request.client is None:
        return False
    try:
        return ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        return False


def create_http_app(
    dispatcher: MemoryServiceDispatcher,
    *,
    authenticator: HttpAuthenticator | None = None,
    deployment_mode: DeploymentMode = DeploymentMode.SHARED,
    test_only_no_auth: TestOnlyLoopbackNoAuth | None = None,
) -> FastAPI:
    """Create an ASGI app; the caller must separately choose whether to bind it."""

    if authenticator is None and test_only_no_auth is None:
        raise ValueError(
            "HTTP authentication is required unless explicit test-only loopback mode is used"
        )
    if test_only_no_auth is not None and deployment_mode is DeploymentMode.SHARED:
        raise ValueError("test-only no-auth mode is prohibited for shared deployments")
    if authenticator is not None and test_only_no_auth is not None:
        raise ValueError("select authenticated mode or test-only no-auth mode, not both")

    app = FastAPI(title="Sys4AI Memory Service", version=API_VERSION)
    app.state.network_listener_started = False
    app.state.deployment_mode = deployment_mode.value
    app.state.security_label = (
        "authenticated shared deployment"
        if test_only_no_auth is None
        else test_only_no_auth.security_label
    )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, _error: RequestValidationError) -> JSONResponse:
        trace_id = safe_trace_id(request.headers.get("x-trace-id"))
        return _json_response(
            error_envelope(trace_id, ErrorCategory.SCHEMA_INVALID),
            status_code=422,
        )

    def endpoint_for(
        action: InterfaceAction,
    ) -> Callable[[str, HttpInvocation, Request], Coroutine[Any, Any, JSONResponse]]:
        async def endpoint(
            project_id: str,
            invocation: HttpInvocation,
            request: Request,
        ) -> JSONResponse:
            trace_id = invocation.trace_id or safe_trace_id(request.headers.get("x-trace-id"))
            if authenticator is not None:
                try:
                    identity = InterfaceIdentity.model_validate(
                        authenticator.authenticate(request.headers)
                    )
                except Exception:  # noqa: BLE001 - transport authentication fails closed
                    return _json_response(
                        error_envelope(trace_id, ErrorCategory.PERMISSION_DENIED),
                        status_code=401,
                    )
            else:
                assert test_only_no_auth is not None
                if not _is_loopback(request):
                    return _json_response(
                        error_envelope(trace_id, ErrorCategory.PERMISSION_DENIED),
                        status_code=403,
                    )
                if (
                    project_id != test_only_no_auth.project_id
                    or invocation.dataset_id != test_only_no_auth.dataset_id
                ):
                    return _json_response(
                        error_envelope(trace_id, ErrorCategory.AUTHORITY_VIOLATION),
                        status_code=403,
                    )
                identity = test_only_no_auth.identity
            try:
                authorization = project_authorization(
                    identity,
                    project_id=project_id,
                    dataset_id=invocation.dataset_id,
                    scope=invocation.scope,
                    query_project_ids=invocation.query_project_ids,
                    explicit_cross_project=invocation.explicit_cross_project,
                )
            except (ValidationError, ValueError, TypeError):
                return _json_response(
                    error_envelope(trace_id, ErrorCategory.AUTHORITY_VIOLATION),
                    status_code=403,
                )
            response = invoke_dispatcher(
                dispatcher,
                operation=action,
                authorization=authorization,
                interface=InterfaceKind.HTTP,
                client_id=invocation.client_id,
                purpose=invocation.purpose,
                payload=invocation.payload,
                idempotency_key=invocation.idempotency_key,
                request_id=invocation.request_id,
                trace_id=trace_id,
            )
            return _json_response(response)

        return endpoint

    for action, path in HTTP_OPERATION_PATHS.items():
        app.add_api_route(
            path,
            endpoint_for(action),
            methods=["POST"],
            name=action.value,
            response_model=None,
        )
    return app
