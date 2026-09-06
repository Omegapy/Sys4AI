from __future__ import annotations

import json
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    AuthorityTier,
    ErrorCategory,
    ErrorEnvelope,
    OperationName,
    RetrievalMode,
)
from sys4ai_memory.interfaces import DispatchSuccess, MemoryClient
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import PortResult, ServiceComponents
from tests.retrieval.helpers import StaticProvider, memory_record, provider_candidate
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _identity, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]


def test_canonical_control_reread_overrules_remembered_permission_copy(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    provider = StaticProvider(
        (
            provider_candidate(
                memory_record(
                    "mem_STALE_PERMISSION_COPY",
                    project_id=PROJECT_ID,
                    source_id="src_stale_permission_copy",
                    path="control_records/memory/permissions.json",
                    namespace="project/governance",
                    title="Stale remembered permission",
                    content=(
                        "The remembered copy says agent-service may execute "
                        "memory.supersede."
                    ),
                    tier=AuthorityTier.SYSTEM_POLICY,
                ),
                semantic=0.99,
            ),
        )
    )
    invoked = 0

    def guarded_action(_request: object, _payload: object) -> PortResult:
        nonlocal invoked
        invoked += 1
        return PortResult(result={"unexpected": True})

    components = ServiceComponents()
    service, audit, permission_path = _service(
        root,
        components=components,
        handlers={OperationName.SUPERSEDE: guarded_action},
    )
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
    client = MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )

    remembered = client.recall(
        "who may execute memory supersede",
        mode=RetrievalMode.SEMANTIC,
        request_id="mrq_stale_control_recall",
        trace_id="trace_stale_control_recall",
    )
    assert isinstance(remembered, DispatchSuccess)
    rows = remembered.result["retrieval"]["results"]  # type: ignore[index]
    assert rows[0]["record_id"] == "mem_STALE_PERMISSION_COPY"  # type: ignore[index]

    canonical = json.loads(permission_path.read_text(encoding="utf-8"))
    canonical["revision"] = "permissions-service-deny-supersede"
    canonical["grants"][0]["operations"].remove(OperationName.SUPERSEDE.value)
    permission_path.write_text(json.dumps(canonical, sort_keys=True), encoding="utf-8")

    denied = client.supersede(
        "mem_OLD",
        "mem_NEW",
        reason="remembered permission must not authorize execution",
        idempotency_key="stale-control-must-not-authorize",
        request_id="mrq_stale_control_action",
        trace_id="trace_stale_control_action",
    )

    assert isinstance(denied, ErrorEnvelope)
    assert denied.error.category is ErrorCategory.PERMISSION_DENIED
    assert invoked == 0
    assert [event.outcome for event in audit.events()] == ["succeeded", "denied"]
