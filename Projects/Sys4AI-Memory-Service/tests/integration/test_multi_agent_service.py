from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from time import sleep

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    ErrorCategory,
    ErrorEnvelope,
    OperationName,
    RetrievalMode,
    RetrievalResult,
)
from sys4ai_memory.interfaces import (
    DispatchRequest,
    DispatchSuccess,
    InterfaceIdentity,
    MemoryClient,
)
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import MemoryService, PortResult, ServiceComponents
from tests.retrieval.helpers import StaticProvider, memory_record, provider_candidate
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


def _identity(principal_id: str) -> InterfaceIdentity:
    return InterfaceIdentity(
        principal_id=principal_id,
        agent_type=f"{principal_id}-type",
        run_id=f"run-{principal_id}",
    )


def _client(service: MemoryService, principal_id: str) -> MemoryClient:
    return MemoryClient(
        service,
        identity=_identity(principal_id),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )


def test_two_agents_share_scoped_evidence_and_service_serializes_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    state_lock = Lock()
    start = Barrier(2)
    active_writes = 0
    maximum_active_writes = 0
    completed_principals: list[str] = []

    def write_handler(request: DispatchRequest, _payload: object) -> PortResult:
        nonlocal active_writes, maximum_active_writes
        principal_id = request.authorization.identity.principal_id
        with state_lock:
            active_writes += 1
            maximum_active_writes = max(maximum_active_writes, active_writes)
        sleep(0.03)
        with state_lock:
            completed_principals.append(principal_id)
            active_writes -= 1
        return PortResult(result={"principal_id": principal_id, "staged": True})

    components = ServiceComponents()
    service, audit, permission_path = _service(
        root,
        components=components,
        handlers={OperationName.PROPOSE: write_handler},
    )
    permissions = json.loads(permission_path.read_text(encoding="utf-8"))
    template = permissions["grants"][0]
    permissions["grants"] = [
        {
            **template,
            "grant_id": f"grant-{principal_id}",
            "principal_id": principal_id,
        }
        for principal_id in ("agent-alpha", "agent-beta")
    ]
    permission_path.write_text(json.dumps(permissions, sort_keys=True), encoding="utf-8")
    provider = StaticProvider(
        (
            provider_candidate(
                memory_record(
                    "mem_SHARED_PROJECT_EVIDENCE",
                    project_id=PROJECT_ID,
                    source_id="src_shared_project_evidence",
                    title="Shared project evidence",
                    content="Both authorized agents receive this project-scoped record.",
                ),
                semantic=0.95,
            ),
        )
    )
    components.retrieval = RetrievalEngine(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        authorizer=AuthorizationService(
            CanonicalPermissionEnvelopeLoader(
                ProjectBoundary(PROJECT_ID, DATASET_ID, root),
                "control_records/memory/permissions.json",
            )
        ),
        provider=provider,
    )
    clients = {
        principal_id: _client(service, principal_id)
        for principal_id in ("agent-alpha", "agent-beta")
    }

    recalled = {
        principal_id: client.recall(
            "shared project evidence",
            mode=RetrievalMode.SEMANTIC,
            request_id=f"mrq_shared_recall_{principal_id}",
            trace_id=f"trace_shared_recall_{principal_id}",
        )
        for principal_id, client in clients.items()
    }
    successful_recalls: list[DispatchSuccess] = []
    for response in recalled.values():
        assert isinstance(response, DispatchSuccess)
        successful_recalls.append(response)
    retrievals = [
        RetrievalResult.model_validate(response.result["retrieval"])
        for response in successful_recalls
    ]
    evidence = [
        result.results[0].model_dump(exclude={"scores", "selection_reason"})
        for result in retrievals
    ]
    assert evidence[0] == evidence[1]
    assert retrievals[0].results[0].record_id == "mem_SHARED_PROJECT_EVIDENCE"

    def propose(principal_id: str) -> object:
        start.wait()
        return clients[principal_id].propose(
            {"record_type": "Observation", "principal_id": principal_id},
            idempotency_key=f"shared-proposal-{principal_id}",
            request_id=f"mrq_shared_proposal_{principal_id}",
            trace_id=f"trace_shared_proposal_{principal_id}",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(propose, ("agent-alpha", "agent-beta"))
        )
    assert all(isinstance(response, DispatchSuccess) for response in responses)
    assert maximum_active_writes == 1
    assert sorted(completed_principals) == ["agent-alpha", "agent-beta"]

    foreign = MemoryClient(
        service,
        identity=_identity("agent-alpha"),
        project_id="foreign-project",
        dataset_id="foreign-dataset",
    ).recall(
        "shared project evidence",
        mode=RetrievalMode.SEMANTIC,
        request_id="mrq_foreign_shared_recall",
        trace_id="trace_foreign_shared_recall",
    )
    assert isinstance(foreign, ErrorEnvelope)
    assert foreign.error.category is ErrorCategory.PERMISSION_DENIED
    assert len(provider.requests) == 2
    outcomes = [event.outcome for event in audit.events()]
    assert outcomes.count("succeeded") == 4
    assert outcomes.count("authorized") == 2
    assert outcomes.count("denied") == 1
