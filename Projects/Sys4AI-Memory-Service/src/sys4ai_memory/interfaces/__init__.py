"""Stable Python, HTTP, CLI, and MCP boundaries for Sys4AI memory."""

from .common import (
    invoke_dispatcher,
    new_request_id,
    new_trace_id,
    project_authorization,
)
from .dispatcher import (
    MemoryServiceDispatcher,
    ServiceDispatchFailure,
    error_envelope,
    safe_dispatch,
)
from .http import (
    HTTP_OPERATION_PATHS,
    HttpAuthenticator,
    HttpInvocation,
    TestOnlyLoopbackNoAuth,
    create_http_app,
)
from .mcp import (
    McpAdapter,
    McpCallAuthorizer,
    McpCallContext,
    McpInvocation,
    McpMode,
    McpToolDescriptor,
)
from .models import (
    MUTATING_ACTIONS,
    OPERATION_INPUT_MODELS,
    AuditContext,
    AuthorizationContext,
    ControlAction,
    DispatchRequest,
    DispatchResponse,
    DispatchSuccess,
    InterfaceAction,
    InterfaceIdentity,
    InterfaceKind,
    LongOperationReference,
    OperationInput,
)
from .python import MemoryClient

__all__ = [
    "HTTP_OPERATION_PATHS",
    "MUTATING_ACTIONS",
    "OPERATION_INPUT_MODELS",
    "AuditContext",
    "AuthorizationContext",
    "ControlAction",
    "DispatchRequest",
    "DispatchResponse",
    "DispatchSuccess",
    "HttpAuthenticator",
    "HttpInvocation",
    "InterfaceAction",
    "InterfaceIdentity",
    "InterfaceKind",
    "LongOperationReference",
    "McpAdapter",
    "McpCallAuthorizer",
    "McpCallContext",
    "McpInvocation",
    "McpMode",
    "McpToolDescriptor",
    "MemoryClient",
    "MemoryServiceDispatcher",
    "OperationInput",
    "ServiceDispatchFailure",
    "TestOnlyLoopbackNoAuth",
    "create_http_app",
    "error_envelope",
    "invoke_dispatcher",
    "new_request_id",
    "new_trace_id",
    "project_authorization",
    "safe_dispatch",
]
