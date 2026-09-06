from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.cli import main
from sys4ai_memory.contracts import McpToolName, OperationName, RetrievalMode
from sys4ai_memory.interfaces import (
    DispatchSuccess,
    McpAdapter,
    McpCallContext,
    MemoryClient,
    create_http_app,
)
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import PortResult, ServiceComponents
from tests.interfaces.helpers import RecordingMcpAuthorizer, StaticAuthenticator
from tests.retrieval.helpers import StaticProvider, memory_record, provider_candidate
from tests.service.test_dispatcher import (
    DATASET_ID,
    PROJECT_ID,
    _identity,
    _service,
)

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


def test_python_http_cli_and_mcp_reach_one_authorized_audited_service(
    tmp_path: Path,
) -> None:
    calls = 0

    def health_handler(_request: object, _payload: object) -> PortResult:
        nonlocal calls
        calls += 1
        return PortResult(result={"route": "guarded-service", "healthy": True})

    service, sink, _ = _service(
        tmp_path.resolve(),
        handlers={OperationName.HEALTH: health_handler},
    )
    identity = _identity()
    python = MemoryClient(
        service,
        identity=identity,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    ).health(request_id="mrq_python_integration", trace_id="trace_python_integration")

    app = create_http_app(service, authenticator=StaticAuthenticator(identity))
    http = TestClient(app).post(
        f"/v1/projects/{PROJECT_ID}/health",
        json={
            "dataset_id": DATASET_ID,
            "scope": {
                "level": "project",
                "scope_id": PROJECT_ID,
                "parent_scopes": [],
            },
            "query_project_ids": [PROJECT_ID],
            "client_id": "http-integration",
            "purpose": "verify guarded service",
            "request_id": "mrq_http_integration",
            "trace_id": "trace_http_integration",
            "payload": {"detailed": False},
        },
    )

    cli_output = StringIO()
    cli_exit = main(
        (
            "--project-id",
            PROJECT_ID,
            "--dataset-id",
            DATASET_ID,
            "--principal-id",
            identity.principal_id,
            "--agent-type",
            identity.agent_type,
            "--run-id",
            identity.run_id,
            "health",
            "--request-id",
            "mrq_cli_integration",
            "--trace-id",
            "trace_cli_integration",
        ),
        dispatcher=service,
        stdout=cli_output,
    )

    authorization = MemoryClient(
        service,
        identity=identity,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    ).authorization
    mcp = McpAdapter(service, authorizer=RecordingMcpAuthorizer())
    mcp_result = mcp.call(
        McpToolName.HEALTH.value,
        {
            "request_id": "mrq_mcp_integration",
            "trace_id": "trace_mcp_integration",
            "payload": {"detailed": False},
        },
        context=McpCallContext(
            authorization=authorization,
            purpose="verify guarded service",
        ),
    )

    assert isinstance(python, DispatchSuccess)
    assert http.status_code == 200
    assert cli_exit == 0
    assert isinstance(mcp_result, DispatchSuccess)
    results = (
        python.result,
        http.json()["result"],
        json.loads(cli_output.getvalue())["result"],
        mcp_result.result,
    )
    assert all(result == {"route": "guarded-service", "healthy": True} for result in results)
    assert calls == 4
    assert len(sink.events()) == 4
    assert {event.operation for event in sink.events()} == {"memory.health"}
    assert app.state.network_listener_started is False


def test_four_interfaces_recall_the_same_service_owned_evidence(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    provider = StaticProvider(
        (
            provider_candidate(
                memory_record(
                    "mem_INTERFACE_INDEPENDENCE",
                    project_id=PROJECT_ID,
                    title="Interface-independent evidence",
                    content="One service-owned record is available to every public adapter.",
                ),
                semantic=0.93,
            ),
        )
    )
    components = ServiceComponents()
    service, sink, _ = _service(root, components=components)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=AuthorizationService(
            CanonicalPermissionEnvelopeLoader(
                boundary,
                "control_records/memory/permissions.json",
            )
        ),
        provider=provider,
    )
    identity = _identity()
    client = MemoryClient(
        service,
        identity=identity,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )
    authorization = client.authorization
    request_id = "mrq_interface_independent_recall"
    trace_id = "trace_interface_independent_recall"
    query = "interface-independent project evidence"
    python = client.recall(
        query,
        mode=RetrievalMode.SEMANTIC,
        request_id=request_id,
        trace_id=trace_id,
    )

    app = create_http_app(service, authenticator=StaticAuthenticator(identity))
    http = TestClient(app).post(
        f"/v1/projects/{PROJECT_ID}/recall",
        json={
            "dataset_id": DATASET_ID,
            "scope": {
                "level": "project",
                "scope_id": PROJECT_ID,
                "parent_scopes": [],
            },
            "query_project_ids": [PROJECT_ID],
            "client_id": "http-interface-independent",
            "purpose": "recall service-owned evidence",
            "request_id": request_id,
            "trace_id": trace_id,
            "payload": {
                "query": query,
                "mode": "semantic",
                "limit": 10,
                "namespaces": [],
                "current_only": True,
                "synthesize": False,
            },
        },
    )

    cli_output = StringIO()
    cli_exit = main(
        (
            "--project-id",
            PROJECT_ID,
            "--dataset-id",
            DATASET_ID,
            "--principal-id",
            identity.principal_id,
            "--agent-type",
            identity.agent_type,
            "--run-id",
            identity.run_id,
            "recall",
            query,
            "--mode",
            "semantic",
            "--request-id",
            request_id,
            "--trace-id",
            trace_id,
        ),
        dispatcher=service,
        stdout=cli_output,
    )

    mcp = McpAdapter(service, authorizer=RecordingMcpAuthorizer())
    mcp_result = mcp.call(
        McpToolName.RECALL.value,
        {
            "request_id": request_id,
            "trace_id": trace_id,
            "payload": {
                "query": query,
                "mode": "semantic",
                "limit": 10,
                "namespaces": [],
                "current_only": True,
                "synthesize": False,
            },
        },
        context=McpCallContext(
            authorization=authorization,
            purpose="recall service-owned evidence",
        ),
    )

    assert isinstance(python, DispatchSuccess)
    assert http.status_code == 200
    assert cli_exit == 0
    assert isinstance(mcp_result, DispatchSuccess)
    results = (
        python.result,
        http.json()["result"],
        json.loads(cli_output.getvalue())["result"],
        mcp_result.result,
    )
    normalized = tuple(json.loads(json.dumps(result, sort_keys=True)) for result in results)
    assert all(set(result) == set(normalized[0]) for result in normalized)

    def evidence_projection(result: dict[str, object]) -> dict[str, object]:
        retrieval = result["retrieval"]
        assert isinstance(retrieval, dict)
        rows = retrieval["results"]
        assert isinstance(rows, list)
        return {
            "query": retrieval["query"],
            "mode": retrieval["mode"],
            "evidence_state": retrieval["evidence_state"],
            "results": [
                {
                    key: row[key]
                    for key in (
                        "record_id",
                        "record_type",
                        "title",
                        "content",
                        "source",
                        "authority",
                        "lifecycle",
                    )
                }
                for row in rows
                if isinstance(row, dict)
            ],
        }

    projected = tuple(evidence_projection(result) for result in normalized)
    assert all(result == projected[0] for result in projected)
    retrieval = normalized[0]["retrieval"]
    assert retrieval["results"][0]["record_id"] == "mem_INTERFACE_INDEPENDENCE"
    assert len(provider.requests) == 4
    assert len(sink.events()) == 4
    assert {event.operation for event in sink.events()} == {OperationName.RECALL.value}
    assert app.state.network_listener_started is False
