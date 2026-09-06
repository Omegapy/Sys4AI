"""In-memory interface fakes; no provider, storage, or network is used."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import JsonValue

from sys4ai_memory.contracts import McpToolDefinition, OperationName
from sys4ai_memory.interfaces import (
    AuthorizationContext,
    ControlAction,
    DispatchRequest,
    DispatchResponse,
    DispatchSuccess,
    InterfaceIdentity,
    LongOperationReference,
    project_authorization,
)
from sys4ai_memory.observability import LONG_RUNNING_OPERATIONS, OperationState


class RecordingDispatcher:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.requests: list[DispatchRequest] = []
        self.failure = failure

    def dispatch(self, request: DispatchRequest) -> DispatchResponse:
        self.requests.append(request)
        if self.failure is not None:
            raise self.failure
        status = None
        if (
            isinstance(request.operation, OperationName)
            and request.operation in LONG_RUNNING_OPERATIONS
        ):
            status = LongOperationReference(
                operation_id=f"op_{request.operation.name.lower()}",
                project_id=request.authorization.project_id,
                operation=request.operation,
                trace_id=request.trace_id,
                state=OperationState.PENDING,
                retry_safe=True,
                retry_after_seconds=1,
            )
        result: dict[str, JsonValue] = {
            "accepted": True,
            "operation": request.operation.value,
        }
        if request.operation is ControlAction.OPERATION_STATUS:
            result["state"] = "running"
            result["retry_safe"] = True
        return DispatchSuccess(
            operation=request.operation,
            project_id=request.authorization.project_id,
            request_id=request.request_id,
            trace_id=request.trace_id,
            result=result,
            operation_status=status,
        )


class StaticAuthenticator:
    def __init__(self, identity: InterfaceIdentity) -> None:
        self.identity = identity
        self.calls = 0

    def authenticate(self, headers: Mapping[str, str]) -> InterfaceIdentity:
        del headers
        self.calls += 1
        return self.identity


class RecordingMcpAuthorizer:
    def __init__(self, *, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[str] = []

    def authorize(
        self,
        authorization: AuthorizationContext,
        tool: McpToolDefinition,
    ) -> bool:
        del authorization
        self.calls.append(tool.name.value)
        return self.allowed


IDENTITY = InterfaceIdentity(
    principal_id="agent_test",
    agent_type="test-agent",
    run_id="run_test",
)
AUTHORIZATION = project_authorization(
    IDENTITY,
    project_id="project-alpha",
    dataset_id="dataset-alpha",
)
REQUEST_ID = "mrq_interface_test"
TRACE_ID = "trace_interface_test"
