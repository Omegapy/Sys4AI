from __future__ import annotations

import json
from io import StringIO

from fastapi.testclient import TestClient

from sys4ai_memory.cli import main
from sys4ai_memory.contracts import McpToolName
from sys4ai_memory.interfaces import (
    DispatchSuccess,
    McpAdapter,
    McpCallContext,
    MemoryClient,
    create_http_app,
)
from tests.cli.test_cli import BASE
from tests.interfaces.helpers import (
    AUTHORIZATION,
    IDENTITY,
    REQUEST_ID,
    TRACE_ID,
    RecordingDispatcher,
    RecordingMcpAuthorizer,
    StaticAuthenticator,
)


def test_python_http_cli_and_mcp_share_one_dispatch_shape() -> None:
    dispatcher = RecordingDispatcher()
    python_client = MemoryClient(
        dispatcher,
        identity=IDENTITY,
        project_id="project-alpha",
        dataset_id="dataset-alpha",
    )
    python_response = python_client.recall(
        "source authority",
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
    )

    http_app = create_http_app(dispatcher, authenticator=StaticAuthenticator(IDENTITY))
    http_response = TestClient(http_app).post(
        "/v1/projects/project-alpha/recall",
        json={
            "dataset_id": "dataset-alpha",
            "scope": {
                "level": "project",
                "scope_id": "project-alpha",
                "parent_scopes": [],
            },
            "query_project_ids": ["project-alpha"],
            "client_id": "http-parity",
            "purpose": "recall source-backed memory",
            "request_id": REQUEST_ID,
            "trace_id": TRACE_ID,
            "payload": {
                "query": "source authority",
                "mode": "hybrid",
                "limit": 10,
                "namespaces": [],
                "current_only": True,
            },
        },
    )

    cli_output = StringIO()
    cli_exit = main(
        (
            *BASE,
            "recall",
            "source authority",
            "--request-id",
            REQUEST_ID,
            "--trace-id",
            TRACE_ID,
        ),
        dispatcher=dispatcher,
        stdout=cli_output,
    )

    mcp = McpAdapter(dispatcher, authorizer=RecordingMcpAuthorizer())
    mcp_response = mcp.call(
        McpToolName.RECALL.value,
        {
            "request_id": REQUEST_ID,
            "trace_id": TRACE_ID,
            "payload": {
                "query": "source authority",
                "mode": "hybrid",
                "limit": 10,
                "namespaces": [],
                "current_only": True,
            },
        },
        context=McpCallContext(
            authorization=AUTHORIZATION,
            purpose="recall source-backed memory",
        ),
    )

    assert isinstance(python_response, DispatchSuccess)
    assert http_response.status_code == 200
    assert cli_exit == 0
    assert isinstance(mcp_response, DispatchSuccess)
    assert json.loads(cli_output.getvalue())["request_id"] == REQUEST_ID
    assert len(dispatcher.requests) == 4
    baseline = dispatcher.requests[0]
    for request in dispatcher.requests[1:]:
        assert request.operation == baseline.operation
        assert request.request_id == baseline.request_id
        assert request.trace_id == baseline.trace_id
        assert request.authorization == baseline.authorization
        assert request.payload == baseline.payload
        assert request.idempotency_key == baseline.idempotency_key
    assert [request.audit.interface.value for request in dispatcher.requests] == [
        "python",
        "http",
        "cli",
        "mcp",
    ]

