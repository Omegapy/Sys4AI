from __future__ import annotations

from collections.abc import Mapping

from pydantic import JsonValue

from sys4ai_memory.contracts import (
    MCP_TOOL_CATALOG,
    ErrorCategory,
    ErrorEnvelope,
    McpToolName,
)
from sys4ai_memory.interfaces import (
    DispatchSuccess,
    McpAdapter,
    McpCallContext,
    McpMode,
)
from tests.interfaces.helpers import (
    AUTHORIZATION,
    REQUEST_ID,
    TRACE_ID,
    RecordingDispatcher,
    RecordingMcpAuthorizer,
)


def _invocation(
    payload: Mapping[str, JsonValue], *, idempotency_key: str | None = None
) -> dict[str, JsonValue]:
    return {
        "request_id": REQUEST_ID,
        "trace_id": TRACE_ID,
        "idempotency_key": idempotency_key,
        "payload": dict(payload),
    }


def test_mcp_inventories_match_default_read_only_and_administrative_policy() -> None:
    dispatcher = RecordingDispatcher()
    authorizer = RecordingMcpAuthorizer()
    default = McpAdapter(dispatcher, authorizer=authorizer)
    read_only = McpAdapter(dispatcher, authorizer=authorizer, mode=McpMode.READ_ONLY)
    administrative = McpAdapter(
        dispatcher,
        authorizer=authorizer,
        mode=McpMode.ADMINISTRATIVE,
    )

    assert {tool.name for tool in default.tools()} == {
        McpToolName.HEALTH,
        McpToolName.RECALL,
        McpToolName.GET,
        McpToolName.GRAPH,
        McpToolName.PROPOSE,
        McpToolName.EXPLAIN,
    }
    assert all(tool.annotations.read_only for tool in read_only.tools())
    assert all(not tool.annotations.mutating for tool in read_only.tools())
    assert len(read_only.tools()) == 5
    assert {tool.name for tool in administrative.tools()} == set(McpToolName)
    assert len(administrative.tools()) == len(MCP_TOOL_CATALOG) == 12


def test_mcp_tool_descriptors_preserve_narrow_catalog_annotations() -> None:
    adapter = McpAdapter(
        RecordingDispatcher(),
        authorizer=RecordingMcpAuthorizer(),
        mode=McpMode.ADMINISTRATIVE,
    )
    expected = {tool.name: tool for tool in MCP_TOOL_CATALOG}

    for descriptor in adapter.tools():
        definition = expected[descriptor.name]
        assert descriptor.description == definition.description
        assert descriptor.annotations == definition.annotations
        assert descriptor.privileged == definition.privileged
        assert descriptor.input_schema["additionalProperties"] is False
        required = descriptor.input_schema["required"]
        assert isinstance(required, list)
        if descriptor.annotations.mutating:
            assert "idempotency_key" in required


def test_mcp_hidden_destructive_tool_is_denied_before_authorization_or_dispatch() -> None:
    dispatcher = RecordingDispatcher()
    authorizer = RecordingMcpAuthorizer()
    adapter = McpAdapter(dispatcher, authorizer=authorizer)

    response = adapter.call(
        McpToolName.FORGET.value,
        _invocation(
            {
                "record_ids": ["mem_ALPHA"],
                "action": "expire",
                "reason": "retention",
                "execute": False,
            },
            idempotency_key="forget-key",
        ),
        context=McpCallContext(authorization=AUTHORIZATION),
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.PERMISSION_DENIED
    assert not authorizer.calls
    assert not dispatcher.requests


def test_default_mcp_can_propose_without_exposing_destructive_tools() -> None:
    dispatcher = RecordingDispatcher()
    authorizer = RecordingMcpAuthorizer()
    adapter = McpAdapter(dispatcher, authorizer=authorizer)

    response = adapter.call(
        McpToolName.PROPOSE.value,
        _invocation(
            {"proposal": {"record_type": "Observation"}},
            idempotency_key="default-propose-key",
        ),
        context=McpCallContext(authorization=AUTHORIZATION),
    )

    assert isinstance(response, DispatchSuccess)
    tools = {tool.name: tool for tool in adapter.tools()}
    assert McpToolName.PROPOSE in tools
    assert tools[McpToolName.PROPOSE].annotations.mutating
    assert not tools[McpToolName.PROPOSE].annotations.destructive
    assert not any(tool.annotations.destructive for tool in tools.values())
    assert authorizer.calls == [McpToolName.PROPOSE.value]
    assert dispatcher.requests[0].operation.value == "memory.propose"


def test_mcp_administrative_tools_still_require_per_call_authorization() -> None:
    dispatcher = RecordingDispatcher()
    authorizer = RecordingMcpAuthorizer(allowed=False)
    adapter = McpAdapter(
        dispatcher,
        authorizer=authorizer,
        mode=McpMode.ADMINISTRATIVE,
    )

    response = adapter.call(
        McpToolName.REBUILD.value,
        _invocation({"preview_only": True}, idempotency_key="rebuild-key"),
        context=McpCallContext(authorization=AUTHORIZATION),
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.PERMISSION_DENIED
    assert authorizer.calls == [McpToolName.REBUILD.value]
    assert not dispatcher.requests


def test_mcp_administrative_authorized_call_preserves_ids_and_status() -> None:
    dispatcher = RecordingDispatcher()
    authorizer = RecordingMcpAuthorizer()
    adapter = McpAdapter(
        dispatcher,
        authorizer=authorizer,
        mode=McpMode.ADMINISTRATIVE,
    )

    response = adapter.call(
        McpToolName.REBUILD.value,
        _invocation({"preview_only": True}, idempotency_key="rebuild-key"),
        context=McpCallContext(authorization=AUTHORIZATION),
    )

    assert isinstance(response, DispatchSuccess)
    assert response.request_id == REQUEST_ID
    assert response.trace_id == TRACE_ID
    assert response.operation_status is not None
    assert response.operation_status.retry_safe is True
    assert dispatcher.requests[0].audit.interface.value == "mcp"


def test_mcp_read_only_inventory_cannot_expose_propose() -> None:
    adapter = McpAdapter(
        RecordingDispatcher(),
        authorizer=RecordingMcpAuthorizer(),
        mode=McpMode.READ_ONLY,
    )

    assert McpToolName.PROPOSE not in {tool.name for tool in adapter.tools()}
