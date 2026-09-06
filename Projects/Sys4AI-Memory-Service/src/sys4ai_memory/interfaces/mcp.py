"""Framework-neutral MCP catalog and call adapter with fail-closed tool exposure."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Annotated, Protocol

from pydantic import Field, JsonValue, ValidationError

from sys4ai_memory.contracts import (
    API_VERSION,
    MCP_TOOL_CATALOG,
    SCHEMA_VERSION,
    ErrorCategory,
    McpAnnotations,
    McpToolDefinition,
    McpToolName,
)
from sys4ai_memory.contracts._base import (
    ApiVersion,
    ContractModel,
    RequestId,
    SchemaVersion,
    StableIdentifier,
    TraceId,
)

from .common import invoke_dispatcher, safe_trace_id
from .dispatcher import MemoryServiceDispatcher, error_envelope
from .models import (
    OPERATION_INPUT_MODELS,
    AuthorizationContext,
    DispatchResponse,
    InterfaceKind,
)


class McpMode(StrEnum):
    DEFAULT = "default"
    READ_ONLY = "read-only"
    ADMINISTRATIVE = "administrative"


class McpCallAuthorizer(Protocol):
    """Independent per-call MCP gate; canonical authorization still occurs downstream."""

    def authorize(
        self,
        authorization: AuthorizationContext,
        tool: McpToolDefinition,
    ) -> bool: ...


class McpCallContext(ContractModel):
    authorization: AuthorizationContext
    client_id: StableIdentifier = "sys4ai-mcp-client"
    purpose: str = "agent memory tool call"


class McpInvocation(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    request_id: RequestId | None = None
    trace_id: TraceId | None = None
    idempotency_key: Annotated[str, Field(min_length=1, max_length=512)] | None = None
    payload: dict[str, JsonValue]


class McpToolDescriptor(ContractModel):
    schema_version: SchemaVersion = SCHEMA_VERSION
    api_version: ApiVersion = API_VERSION
    name: McpToolName
    operation: str
    description: str
    input_schema: dict[str, JsonValue]
    annotations: McpAnnotations
    privileged: bool


def _tool_input_schema(tool: McpToolDefinition) -> dict[str, JsonValue]:
    payload_schema = OPERATION_INPUT_MODELS[tool.operation].model_json_schema(mode="validation")
    required: list[JsonValue] = ["payload"]
    if tool.annotations.mutating:
        required.append("idempotency_key")
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION, "default": SCHEMA_VERSION},
            "api_version": {"const": API_VERSION, "default": API_VERSION},
            "request_id": {"type": ["string", "null"], "pattern": "^mrq_"},
            "trace_id": {"type": ["string", "null"], "pattern": "^trace_"},
            "idempotency_key": {"type": ["string", "null"], "minLength": 1},
            "payload": payload_schema,
        },
        "required": required,
    }


def _enabled_tools(mode: McpMode) -> tuple[McpToolDefinition, ...]:
    if mode is McpMode.ADMINISTRATIVE:
        return MCP_TOOL_CATALOG
    if mode is McpMode.READ_ONLY:
        return tuple(tool for tool in MCP_TOOL_CATALOG if tool.annotations.read_only)
    return tuple(tool for tool in MCP_TOOL_CATALOG if tool.default_enabled)


class McpAdapter:
    """Expose only the tools allowed by one explicit MCP deployment mode."""

    def __init__(
        self,
        dispatcher: MemoryServiceDispatcher,
        *,
        authorizer: McpCallAuthorizer,
        mode: McpMode = McpMode.DEFAULT,
    ) -> None:
        self._dispatcher = dispatcher
        self._authorizer = authorizer
        self._mode = mode
        self._definitions = {tool.name: tool for tool in _enabled_tools(mode)}

    @property
    def mode(self) -> McpMode:
        return self._mode

    def tools(self) -> tuple[McpToolDescriptor, ...]:
        return tuple(
            McpToolDescriptor(
                name=definition.name,
                operation=definition.operation.value,
                description=definition.description,
                input_schema=_tool_input_schema(definition),
                annotations=definition.annotations,
                privileged=definition.privileged,
            )
            for definition in self._definitions.values()
        )

    def call(
        self,
        tool_name: str,
        invocation: Mapping[str, JsonValue],
        *,
        context: McpCallContext,
    ) -> DispatchResponse:
        trace_id = safe_trace_id(invocation.get("trace_id"))
        try:
            name = McpToolName(tool_name)
            definition = self._definitions[name]
            call = McpInvocation.model_validate(invocation)
        except (ValueError, KeyError, ValidationError, TypeError):
            return error_envelope(trace_id, ErrorCategory.PERMISSION_DENIED)
        try:
            allowed = self._authorizer.authorize(context.authorization, definition)
        except Exception:  # noqa: BLE001 - transport authorization fails closed
            allowed = False
        if not allowed:
            return error_envelope(trace_id, ErrorCategory.PERMISSION_DENIED)
        return invoke_dispatcher(
            self._dispatcher,
            operation=definition.operation,
            authorization=context.authorization,
            interface=InterfaceKind.MCP,
            client_id=context.client_id,
            purpose=context.purpose,
            payload=call.payload,
            idempotency_key=call.idempotency_key,
            request_id=call.request_id,
            trace_id=call.trace_id or trace_id,
        )
